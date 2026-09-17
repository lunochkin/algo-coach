import json
import re
import sys
import time
from pathlib import Path
from typing import Literal, NamedTuple

import pytest
from fastapi.testclient import TestClient

from algo_coach.broker import create_app
from algo_coach.broker.container import (
    CASE_SLACK_MS,
    IMAGE,
    OUTPUT_PER_CASE,
    STARTUP_MS,
    Execute,
    Finished,
    Stop,
    docker,
)
from algo_coach.runner import child

DOUBLE = "def solve(n):\n    return n * 2\n"
RUN = {"code": DOUBLE, "args": [[1], [2]], "cap_ms": 3000}
RETURNED = b'{"outcome": "returned", "value": "2", "elapsed_ms": 0}\n'
CRASHED = b'{"outcome": "crashed", "value": null, "elapsed_ms": 0, "error": "no"}\n'
TIMEOUT = {"outcome": "timeout", "value": None, "elapsed_ms": None, "error": None}


class Sent(NamedTuple):
    argv: list[str]
    stdin: bytes
    limit: int
    seconds: float


class Recorded:
    """Answers every command with one fixed ending, and keeps what it was
    sent."""

    def __init__(
        self,
        stdout: bytes = b"",
        returncode: int = 0,
        stderr: bytes = b"",
        how: Literal["exited", "overflowed", "expired"] = "exited",
    ) -> None:
        self.finished = Finished(how, returncode, stdout, stderr)
        self.calls: list[Sent] = []

    def __call__(self, argv: list[str], stdin: bytes, limit: int, seconds: float) -> Finished:
        self.calls.append(Sent(argv, stdin, limit, seconds))
        return self.finished


class Stopped:
    """Keeps the name of every container the broker stopped."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def __call__(self, name: str) -> None:
        self.names.append(name)


def local(argv: list[str], stdin: bytes, limit: int, seconds: float) -> Finished:
    """The container's command run on this machine through the broker's own
    reader, with this interpreter standing in for the image's `python`."""
    _python, *rest = argv[argv.index(IMAGE) + 1 :]
    return docker([sys.executable, *rest], stdin, limit, seconds)


def client(execute: Execute, stop: Stop | None = None) -> TestClient:
    return TestClient(create_app(execute, stop or Stopped(), _nothing, _nothing))


def _nothing() -> None:
    """Stands in for removing leftover containers and pulling the image, which
    a test client entered with `with` would otherwise do against the real
    docker."""


def test_a_starting_broker_clears_leftovers_and_pulls_its_image_before_its_first_run():
    """A broker that died mid-run left its container running, and every run
    starts with `--pull never`, so both happen once, before any run."""
    started: list[str] = []
    app = create_app(
        Recorded(stdout=RETURNED * 2),
        Stopped(),
        lambda: started.append("cleared"),
        lambda: started.append("pulled"),
    )

    with TestClient(app) as broker:
        assert started == ["cleared", "pulled"]
        broker.post("/run", json=RUN)

    assert started == ["cleared", "pulled"]


def test_the_submission_s_image_is_pinned_by_digest():
    """A tag moves under the run a stored verdict was measured by."""
    assert re.fullmatch(r"python:3\.14-slim@sha256:[0-9a-f]{64}", IMAGE)


def test_each_run_s_container_carries_the_label_leftovers_are_found_by():
    assert _holds(_options(one_run().argv), ["--label", "algo-coach.run"])


def test_a_run_answers_a_result_per_case():
    response = client(local).post("/run", json=RUN)

    assert response.status_code == 200
    cases = response.json()["cases"]
    assert [each["outcome"] for each in cases] == ["returned", "returned"]
    assert [json.loads(each["value"]) for each in cases] == [2, 4]


def test_a_run_is_one_docker_run_reading_the_run_on_standard_input():
    """One container per run, and the code reaches it on standard input, so a
    run mounts nothing."""
    recorded = Recorded(stdout=RETURNED * 2)

    client(recorded).post("/run", json=RUN)

    (sent,) = recorded.calls
    assert sent.argv[:2] == ["docker", "run"]
    assert "-i" in sent.argv
    assert json.loads(sent.stdin) == RUN | {"repeats": None, "stop_early": False}


def test_the_container_runs_the_entry_process_s_script_whole():
    """Sent with each run rather than built into the image, so the entry process
    always matches the broker that sent it."""
    argv = one_run().argv

    script = Path(child.__file__).read_text()
    assert argv[argv.index(IMAGE) :] == [IMAGE, "python", "-c", script]


@pytest.mark.parametrize(
    "flag",
    [
        ["--runtime", "runsc"],
        ["--network", "none"],
        ["--read-only"],
        ["--user", "65534:65534"],
        ["--cap-drop", "ALL"],
        ["--security-opt", "no-new-privileges"],
        ["--memory", "512m"],
        ["--memory-swap", "512m"],
        ["--pids-limit", "256"],
        ["--init"],
        ["--env", "ALGO_COACH_SANDBOX=1"],
    ],
)
def test_the_container_starts_confined(flag):
    """Each flag sits among docker's options, before the image. After the image
    it would be an argument to `python`, and the container would start
    unconfined."""
    assert _holds(_options(one_run().argv), flag)


def test_each_run_s_container_has_a_name_of_its_own():
    """The name is how a container outliving its client is killed, so two runs
    sharing one would kill each other's."""
    first, second = (_options(one_run().argv) for _ in range(2))

    names = [options[options.index("--name") + 1] for options in (first, second)]
    assert names[0] != names[1]


def one_run(run: dict[str, object] = RUN) -> Sent:
    recorded = Recorded(stdout=RETURNED * 2)
    client(recorded).post("/run", json=run)
    (sent,) = recorded.calls
    return sent


def _options(argv: list[str]) -> list[str]:
    return argv[: argv.index(IMAGE)]


def _holds(options: list[str], flag: list[str]) -> bool:
    return any(options[at : at + len(flag)] == flag for at in range(len(options)))


@pytest.mark.parametrize("field", ["image", "mounts", "volumes", "flags", "runtime", "network"])
def test_a_field_the_run_does_not_take_is_refused(field):
    """The image, the mounts and the flags are the broker's source alone, and
    every later hardening step would inherit a field a request can set."""
    recorded = Recorded()

    response = client(recorded).post("/run", json=RUN | {field: "anything"})

    assert response.status_code == 422
    assert recorded.calls == []


def test_a_cap_of_nothing_is_refused():
    assert client(Recorded()).post("/run", json=RUN | {"cap_ms": 0}).status_code == 422


def test_a_repeat_count_is_given_per_case_or_not_at_all():
    assert client(Recorded()).post("/run", json=RUN | {"repeats": [1]}).status_code == 422


def test_a_container_exiting_non_zero_answers_no_verdict():
    """Docker's own failure says nothing about the solution, and a stored
    `CRASHED` would reject a sound draft over the runner's defect."""
    recorded = Recorded(returncode=125, stderr=b"Unable to find image")

    response = client(recorded).post("/run", json=RUN)

    assert response.status_code == 500
    assert "125" in response.json()["detail"]


def test_a_run_short_of_a_case_answers_no_verdict():
    """A missing line is the entry process's fault where nothing stopped
    early."""
    response = client(Recorded(stdout=RETURNED)).post("/run", json=RUN)

    assert response.status_code == 500


def test_stop_early_may_answer_fewer_cases():
    code = "def solve(n):\n    raise ValueError('no')\n"

    response = client(local).post("/run", json=RUN | {"code": code, "stop_early": True})

    assert [each["outcome"] for each in response.json()["cases"]] == ["crashed"]


def test_a_run_s_output_limit_grows_with_its_cases():
    """A fixed limit would refuse a sound run only for how many cases it
    carries."""
    two, five = one_run(), one_run(RUN | {"args": [[1]] * 5})

    assert five.limit - two.limit == 3 * OUTPUT_PER_CASE


def test_a_run_whose_output_passes_its_limit_answers_no_verdict():
    """The broker reads what the container writes into its own memory, so a
    return past the limit stops the read instead of holding the machine."""
    code = f"def solve():\n    return 'x' * {2 * OUTPUT_PER_CASE}\n"

    response = client(local).post("/run", json=RUN | {"code": code, "args": [[]]})

    assert response.status_code == 500
    assert "output passed" in response.json()["detail"]


def test_a_run_s_deadline_covers_every_case_s_cap_and_the_container_s_start():
    """Each case's slack sits above the entry process's own, so a sound entry
    reports its timeout before the broker's timer fires."""
    sent = one_run(RUN | {"args": [[1]] * 3, "cap_ms": 500})

    assert sent.seconds == (3 * (500 + CASE_SLACK_MS) + STARTUP_MS) / 1000


def test_an_expired_run_kills_its_container_by_name():
    """The client dying leaves the container running, holding the processes and
    the memory its flags allow."""
    recorded, stopped = Recorded(how="expired"), Stopped()

    client(recorded, stopped).post("/run", json=RUN)

    (sent,) = recorded.calls
    options = _options(sent.argv)
    assert stopped.names == [options[options.index("--name") + 1]]


def test_an_expired_run_answers_each_unreported_case_timeout():
    """A child stuck outside Python never fires its own timer, and the parent's
    timer firing is `TIMEOUT`. A line the kill cut off is no result."""
    recorded = Recorded(stdout=RETURNED + b'{"outcome": "retu', how="expired")

    response = client(recorded).post("/run", json=RUN | {"args": [[1], [2], [3]]})

    assert response.status_code == 200
    first, *rest = response.json()["cases"]
    assert first["outcome"] == "returned"
    assert rest == [TIMEOUT, TIMEOUT]


def test_an_expired_run_under_stop_early_times_out_the_next_case_alone():
    response = client(Recorded(how="expired")).post("/run", json=RUN | {"stop_early": True})

    assert response.json()["cases"] == [TIMEOUT]


def test_an_expired_run_adds_nothing_after_a_case_that_stopped_it_early():
    recorded = Recorded(stdout=CRASHED, how="expired")

    response = client(recorded).post("/run", json=RUN | {"stop_early": True})

    assert [each["outcome"] for each in response.json()["cases"]] == ["crashed"]


def test_output_within_the_limit_is_read_whole_from_both_streams():
    script = "import sys\nsys.stdout.write('x' * 200_000)\nsys.stderr.write('e' * 100_000)\n"

    done = docker([sys.executable, "-c", script], b"", 400_000, 30)

    assert (done.how, done.returncode) == ("exited", 0)
    assert (len(done.stdout), len(done.stderr)) == (200_000, 100_000)


def test_output_past_the_limit_kills_the_command_at_once():
    """Either stream carries what the container writes, and a command still
    writing would otherwise be read until it exits."""
    script = (
        "import sys, time\nsys.stderr.write('e' * 100_000)\nsys.stderr.flush()\ntime.sleep(30)\n"
    )

    started = time.monotonic()
    done = docker([sys.executable, "-c", script], b"", 50_000, 60)

    assert time.monotonic() - started < 10
    assert done.how == "overflowed"
    assert b"passed 50000 bytes" in done.stderr


def test_a_command_past_its_deadline_is_killed_with_what_it_wrote():
    script = "import time\nprint('reported', flush=True)\ntime.sleep(30)\n"

    started = time.monotonic()
    done = docker([sys.executable, "-c", script], b"", 1000, 0.5)

    assert time.monotonic() - started < 10
    assert done.how == "expired"
    assert done.stdout == b"reported\n"


def test_a_command_that_never_reads_its_input_still_meets_the_deadline():
    """A run larger than a pipe holds fills the pipe, so feeding it before the
    read would wait on a command that never reads."""
    started = time.monotonic()
    done = docker(
        [sys.executable, "-c", "import time; time.sleep(30)"], b"x" * (4 << 20), 1000, 0.5
    )

    assert time.monotonic() - started < 10
    assert done.how == "expired"
