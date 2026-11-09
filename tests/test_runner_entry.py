import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from algo_coach.runner import child

DOUBLE = "def solve(n):\n    return n * 2\n"
# the script as the broker sends it: its source, run as `python -c`
SCRIPT = Path(child.__file__).read_text()

# a solution's own count of `solve` calls in its process. A module global
# cannot count them, since every call runs on a fresh module
COUNTED = (
    "import builtins\n"
    "\n"
    "\n"
    "def solve():\n"
    "    builtins.calls = getattr(builtins, 'calls', 0) + 1\n"
    "    return builtins.calls\n"
)


def entered(
    code: str, args: list[list[Any]], **overrides: object
) -> subprocess.CompletedProcess[str]:
    request = {"code": code, "args": args, "cap_ms": 3000, "repeats": None, "stop_early": False}
    return subprocess.run(
        [sys.executable, "-c", SCRIPT],
        input=json.dumps(request | overrides),
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def lines(code: str, args: list[list[Any]], **overrides: object) -> list[dict[str, Any]]:
    return [json.loads(line) for line in entered(code, args, **overrides).stdout.splitlines()]


def test_the_entry_prints_one_line_per_case_in_the_order_given():
    results = lines(DOUBLE, [[1], [2], [3]])

    assert [each["outcome"] for each in results] == ["returned"] * 3
    assert [json.loads(each["value"]) for each in results] == [2, 4, 6]


def test_a_solution_s_output_reaches_no_line_the_broker_parses():
    """The broker parses standard output, and a line the solution printed there
    would be read as a case's result."""
    code = (
        "import os, sys\n"
        "\n"
        "\n"
        "def solve():\n"
        '    print(\'{"outcome": "crashed"}\')\n'
        "    os.write(1, b'raw\\n')\n"
        "    sys.stderr.write('noise')\n"
        "    return 1\n"
    )

    done = entered(code, [[]])

    assert [json.loads(line)["value"] for line in done.stdout.splitlines()] == ["1"]
    assert done.stderr == ""


def test_each_case_runs_in_a_process_of_its_own():
    """`corpus.md` requires that no case observes another, and a solution
    writing to process-wide state would otherwise carry it to the next case."""
    assert [each["value"] for each in lines(COUNTED, [[], [], []])] == ["1", "1", "1"]


def test_repeats_are_read_per_case():
    assert [each["value"] for each in lines(COUNTED, [[], []], repeats=[1, 3])] == ["1", "3"]


def test_a_case_past_the_cap_times_out():
    (result,) = lines("def solve():\n    while True:\n        pass\n", [[]], cap_ms=200)

    assert result["outcome"] == "timeout"


def test_a_case_whose_own_timer_never_fires_is_timed_out_by_the_entry():
    """A solution blocking the alarm never reaches the child's own timeout, and
    would otherwise hold the run past every cap."""
    code = (
        "import signal\n"
        "\n"
        "\n"
        "def solve():\n"
        "    signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGALRM])\n"
        "    while True:\n"
        "        pass\n"
    )

    (result,) = lines(code, [[]], cap_ms=100)

    assert result == {"outcome": "timeout", "value": None, "elapsed_ms": None}


def test_a_case_killed_by_a_signal_crashed():
    """A segfault and a kill under memory pressure both land here, and neither
    writes a result."""
    code = "import os, signal\n\n\ndef solve():\n    os.kill(os.getpid(), signal.SIGKILL)\n"

    (result,) = lines(code, [[]])

    assert result["outcome"] == "crashed"
    assert result["error"] == "killed by signal 9"


def test_stop_early_stops_at_the_first_case_that_yielded_nothing():
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    results = lines(code, [[1], [2], [3]], stop_early=True)

    assert [each["outcome"] for each in results] == ["returned", "crashed"]


def test_a_process_the_solution_leaves_behind_neither_holds_the_run_nor_outlives_it(tmp_path):
    """A forked process inherits the channel the result travels on, so waiting
    for that channel to close would wait for the forked process too."""
    spawned = tmp_path / "pid"
    code = (
        "import os, time\n"
        "\n"
        "\n"
        "def solve():\n"
        "    pid = os.fork()\n"
        "    if pid == 0:\n"
        "        time.sleep(30)\n"
        "        os._exit(0)\n"
        f"    open({str(spawned)!r}, 'w').write(str(pid))\n"
        "    return 1\n"
    )

    started = time.monotonic()
    (result,) = lines(code, [[]])

    assert result["value"] == "1"
    assert time.monotonic() - started < 10
    pid = int(spawned.read_text())
    for _ in range(50):
        if not _alive(pid):
            break
        time.sleep(0.05)
    assert not _alive(pid)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError, PermissionError:
        return False
    return True
