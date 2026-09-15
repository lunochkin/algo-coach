import json
import shutil
import subprocess
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from algo_coach.broker import create_app
from algo_coach.broker.container import IMAGE, kill, remove_leftovers

DOUBLE = "def solve(n):\n    return n * 2\n"

# one case per confinement the broker's flags claim, answered from inside the
# container. /var/tmp is writable by anyone and sits on the root filesystem,
# where gVisor mounts a tmpfs over /tmp whatever the root allows
PROBES = (
    "import os, socket\n"
    "\n"
    "\n"
    "def solve(probe):\n"
    "    try:\n"
    "        if probe == 'user':\n"
    "            return os.getuid()\n"
    "        if probe == 'network':\n"
    "            socket.create_connection(('1.1.1.1', 53), timeout=1).close()\n"
    "        if probe == 'write':\n"
    "            open('/var/tmp/probe', 'w').close()\n"
    "    except OSError:\n"
    "        return 'refused'\n"
    "    return 'allowed'\n"
)

# a case that exhausts memory, a case that spawns without bound, and a case
# after both that asks for nothing
LIMITS = (
    "import os, time\n"
    "\n"
    "\n"
    "def solve(probe):\n"
    "    if probe == 'memory':\n"
    "        return len(bytearray(1 << 30))\n"
    "    if probe == 'processes':\n"
    "        try:\n"
    "            for _ in range(200):\n"
    "                if os.fork() == 0:\n"
    "                    time.sleep(10)\n"
    "                    os._exit(0)\n"
    "        except OSError:\n"
    "            return 'refused'\n"
    "        return 'allowed'\n"
    "    return 'answered'\n"
)

# stops the entry process, so no timer inside the container ever fires
STOPS_ENTRY = "import os, signal\n\n\ndef solve():\n    os.kill(os.getppid(), signal.SIGSTOP)\n"


@pytest.fixture(scope="module")
def sandbox() -> TestClient:
    """The broker as deployed: its own executor, starting a container under
    runsc. Never entered with `with`, which would remove the containers the
    other workers' runs are using."""
    if not _runsc():
        pytest.skip("a run's container needs docker's runsc runtime, which runs only on Linux")
    return TestClient(create_app())


def _runsc() -> bool:
    if shutil.which("docker") is None:
        return False
    done = subprocess.run(
        ["docker", "info", "--format", "{{json .Runtimes}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode == 0 and "runsc" in json.loads(done.stdout)


def test_a_run_answers_from_inside_its_container(sandbox: TestClient):
    """The entry process runs as `python -c` on the submission's image, and
    needs nothing written to its read-only root."""
    response = sandbox.post("/run", json={"code": DOUBLE, "args": [[1], [2]], "cap_ms": 3000})

    assert response.status_code == 200, response.text
    assert [json.loads(each["value"]) for each in response.json()["cases"]] == [2, 4]


def test_the_container_holds_the_confinement_its_flags_claim(sandbox: TestClient):
    """A flag in the argument list says nothing about the container it started:
    only a solution inside can show the user, the network and the root."""
    run = {"code": PROBES, "args": [["user"], ["network"], ["write"]], "cap_ms": 3000}

    response = sandbox.post("/run", json=run)

    assert response.status_code == 200, response.text
    values = [json.loads(each["value"]) for each in response.json()["cases"]]
    assert values == [65534, "refused", "refused"]


def test_a_case_past_the_memory_or_process_limit_fails_alone(sandbox: TestClient):
    """The container's limits refuse a case that exhausts memory or spawns
    without bound, and the next case still answers."""
    run = {"code": LIMITS, "args": [["memory"], ["processes"], ["after"]], "cap_ms": 10_000}

    response = sandbox.post("/run", json=run)

    assert response.status_code == 200, response.text
    memory, processes, after = response.json()["cases"]
    assert memory["outcome"] == "crashed"
    assert json.loads(processes["value"]) == "refused"
    assert json.loads(after["value"]) == "answered"


def test_a_run_whose_entry_stops_answering_times_out_and_leaves_no_container(
    sandbox: TestClient,
):
    """Every timer inside the container waits on the stopped entry process, so
    only the broker's own timer and a kill by name end the run."""
    stopped: list[str] = []

    def stop(name: str) -> None:
        stopped.append(name)
        kill(name)

    run = {"code": STOPS_ENTRY, "args": [[], []], "cap_ms": 100}

    response = TestClient(create_app(stop=stop)).post("/run", json=run)

    assert response.status_code == 200, response.text
    assert [each["outcome"] for each in response.json()["cases"]] == ["timeout", "timeout"]
    (name,) = stopped
    assert _gone(name)


def test_leftover_containers_are_removed_running_or_not(sandbox: TestClient):
    """A label of this test's own, since the broker's label would reach the
    containers the other workers' runs are using."""
    label = f"algo-coach.test-{uuid.uuid4().hex}"
    running, exited = (f"algo-coach-leftover-{uuid.uuid4().hex}" for _ in range(2))
    _leftover(running, label, ["sleep", "60"], detach=True)
    _leftover(exited, label, ["true"])

    remove_leftovers(label)

    assert _gone(running)
    assert _gone(exited)


def _leftover(name: str, label: str, command: list[str], *, detach: bool = False) -> None:
    options = ["--pull", "never", "--runtime", "runsc", "--name", name, "--label", label]
    subprocess.run(
        ["docker", "run", *(["--detach"] if detach else []), *options, IMAGE, *command],
        capture_output=True,
        check=True,
    )


def _gone(name: str) -> bool:
    # --rm removes a killed container a moment after the kill returns
    for _ in range(50):
        left = subprocess.run(
            ["docker", "ps", "--all", "--quiet", "--filter", f"name=^/{name}$"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not left.stdout.strip():
            return True
        time.sleep(0.2)
    return False
