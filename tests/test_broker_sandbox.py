import json
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from algo_coach.broker import create_app

DOUBLE = "def solve(n):\n    return n * 2\n"

# one case per confinement the broker's flags claim, answered from inside the
# container. /tmp is writable by anyone, so only a read-only root refuses it
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
    "            open('/tmp/probe', 'w').close()\n"
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


@pytest.fixture(scope="module")
def sandbox() -> TestClient:
    """The broker as deployed: its own executor, starting a container under
    runsc."""
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
