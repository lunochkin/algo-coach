import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from algo_coach.broker import create_app
from algo_coach.broker.container import IMAGE, Execute
from algo_coach.runner import child

DOUBLE = "def solve(n):\n    return n * 2\n"
RUN = {"code": DOUBLE, "args": [[1], [2]], "cap_ms": 3000}
RETURNED = b'{"outcome": "returned", "value": "2", "elapsed_ms": 0}\n'


class Recorded:
    """Answers every run with one fixed process result, and keeps what it was
    sent."""

    def __init__(self, stdout: bytes = b"", returncode: int = 0, stderr: bytes = b"") -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr
        self.calls: list[tuple[list[str], bytes]] = []

    def __call__(self, argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((argv, stdin))
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, self.stderr)


def local(argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    """The container's command run on this machine, with this interpreter
    standing in for the image's `python`."""
    _python, *rest = argv[argv.index(IMAGE) + 1 :]
    return subprocess.run([sys.executable, *rest], input=stdin, capture_output=True, check=False)


def client(execute: Execute) -> TestClient:
    return TestClient(create_app(execute))


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

    ((argv, stdin),) = recorded.calls
    assert argv[:2] == ["docker", "run"]
    assert "-i" in argv
    assert json.loads(stdin) == RUN | {"repeats": None, "stop_early": False}


def test_the_container_runs_the_entry_process_s_script_whole():
    """Sent with each run rather than built into the image, so the entry process
    always matches the broker that sent it."""
    argv = one_run_argv()

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
    ],
)
def test_the_container_starts_confined(flag):
    """Each flag sits among docker's options, before the image. After the image
    it would be an argument to `python`, and the container would start
    unconfined."""
    argv = one_run_argv()
    options = argv[: argv.index(IMAGE)]

    assert any(options[at : at + len(flag)] == flag for at in range(len(options)))


def one_run_argv() -> list[str]:
    recorded = Recorded(stdout=RETURNED * 2)
    client(recorded).post("/run", json=RUN)
    ((argv, _),) = recorded.calls
    return argv


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
