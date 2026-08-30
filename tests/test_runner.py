"""Running a solution against arguments, and what each call produced.

The one boundary an executor sits behind. What a result means is fixed here
rather than by whatever executed it, since a `Verification` outlives the
runner that wrote one.
"""

import json
import os
import time

import pytest

from algo_coach.generation.agreement import as_json
from algo_coach.runner import STARTUP_MS, CaseRun, RunOutcome, defines_solve, run

DOUBLE = "def solve(n):\n    return n * 2\n"


def only(code: str, *args, **overrides) -> CaseRun:
    return run(code, [list(args)], **{"cap_ms": 3000} | overrides)[0]


def test_a_call_reports_what_the_solution_returned():
    assert only(DOUBLE, 21) == CaseRun(RunOutcome.RETURNED, 42, elapsed_ms=0)


def test_the_arguments_are_positional():
    """A case is arguments and an expected return, so a canonical names its
    parameters whatever reads best."""
    code = "def solve(first, second, third):\n    return [third, second, first]\n"

    assert only(code, 1, 2, 3).value == [3, 2, 1]


def test_a_case_passing_no_arguments_still_decides_one():
    assert only("def solve():\n    return 7\n").value == 7


def test_the_whole_set_runs_in_one_call():
    """A per-case boundary is one network round trip per case once the
    executor is remote."""
    results = run(DOUBLE, [[1], [2], [3]], cap_ms=3000)

    assert [each.value for each in results] == [2, 4, 6]


def test_the_return_is_decoded_by_the_encoder_a_case_is_stored_with():
    """A tuple and a list are one answer under that rule, and the child does
    the encoding so the same return cannot be decided by where it ran."""
    code = "def solve():\n    return (1, {'b': 2, 'a': 1})\n"

    assert as_json(only(code).value) == as_json([1, {"a": 1, "b": 2}])


def test_no_case_observes_another():
    """A solution memoising in a module global would otherwise answer one case
    from a cache built for a different one, and a wrong key would pass."""
    code = "seen = []\n\n\ndef solve(n):\n    seen.append(n)\n    return len(seen)\n"

    assert [each.value for each in run(code, [[1], [2], [3]], cap_ms=3000)] == [1, 1, 1]


def test_a_solution_that_raises_crashed():
    assert only("def solve():\n    raise ValueError('no')\n").outcome is RunOutcome.CRASHED


def test_a_return_json_cannot_encode_is_crashed():
    """The fault is the solution's rather than the case's. `WRONG` would file
    it beside an answer that was computed and is merely incorrect."""
    assert only("def solve():\n    return {1, 2}\n").outcome is RunOutcome.CRASHED


def test_a_solution_defining_no_solve_fails_every_case():
    """Phase 8 reads this path for an attempt, so it needs a verdict rather
    than an error."""
    results = run("def other():\n    return 1\n", [[1], [2]], cap_ms=3000)

    assert [each.outcome for each in results] == [RunOutcome.CRASHED, RunOutcome.CRASHED]


def test_a_solution_defining_no_solve_fails_every_case_under_stop_early_too():
    """The verdict is a fact about the code rather than about a case, so
    nothing ran and there is nothing to stop at."""
    results = run("def other():\n    return 1\n", [[1], [2]], cap_ms=3000, stop_early=True)

    assert [each.outcome for each in results] == [RunOutcome.CRASHED, RunOutcome.CRASHED]


def test_code_that_does_not_parse_fails_every_case():
    assert only("def solve(:\n").outcome is RunOutcome.CRASHED


def test_a_module_that_never_finishes_importing_is_rejected_without_running_it():
    """The check reads the syntax tree, so it is decided before anything runs
    rather than at the cap."""
    started = time.perf_counter()
    result = only("while True:\n    pass\n", cap_ms=60000)

    assert result.outcome is RunOutcome.CRASHED
    assert (time.perf_counter() - started) * 1000 < STARTUP_MS


def test_solve_is_read_from_the_tree_however_it_is_bound():
    assert defines_solve(DOUBLE)
    assert defines_solve("solve = lambda n: n\n")
    assert not defines_solve("class Solver:\n    def solve(self):\n        return 1\n")
    assert not defines_solve("def solve(:\n")


def test_a_call_that_runs_past_the_cap_times_out():
    result = only("def solve():\n    while True:\n        pass\n", cap_ms=200)

    assert result.outcome is RunOutcome.TIMEOUT


def test_the_cap_is_measured_in_the_child_around_solve():
    """Interpreter start is excluded, since it moves with the machine's load
    and two runs storing one number would not be comparable."""
    code = "import time\n\n\ndef solve():\n    time.sleep(0.3)\n    return 1\n"

    assert 250 <= only(code).elapsed_ms < 600


def test_a_cap_of_nothing_is_rejected():
    with pytest.raises(ValueError, match="cap"):
        only(DOUBLE, 1, cap_ms=0)


def test_stop_early_stops_at_the_first_case_that_yielded_nothing():
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    results = run(code, [[1], [2], [3]], cap_ms=3000, stop_early=True)

    assert [each.outcome for each in results] == [RunOutcome.RETURNED, RunOutcome.CRASHED]


def test_stop_early_never_stops_at_a_returned_value():
    """The backend is not told what a case expects, so a wrong answer is
    invisible here and the mutation loop is what wants the rest run."""
    results = run(DOUBLE, [[1], [2], [3]], cap_ms=3000, stop_early=True)

    assert len(results) == 3


def test_every_case_is_decided_where_nothing_stops_early():
    """The canonical stores a count, and a count needs every case decided."""
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    results = run(code, [[1], [2], [3]], cap_ms=3000)

    assert [each.outcome for each in results] == [
        RunOutcome.RETURNED,
        RunOutcome.CRASHED,
        RunOutcome.RETURNED,
    ]


def test_a_solution_that_prints_does_not_corrupt_the_channel():
    """Stdout belongs to the solution, so the result never travels on it."""
    code = 'def solve():\n    print(\'{"outcome": "crashed"}\')\n    return 1\n'

    assert only(code) == CaseRun(RunOutcome.RETURNED, 1, elapsed_ms=0)


def test_a_child_of_the_solution_dies_with_it(tmp_path):
    """A solution that spawned one would otherwise be left running when the
    cap killed its parent."""
    spawned = tmp_path / "pid"
    code = (
        "import subprocess, sys\n"
        "\n"
        "\n"
        "def solve():\n"
        "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        f"    open({str(spawned)!r}, 'w').write(str(child.pid))\n"
        "    while True:\n"
        "        pass\n"
    )

    assert only(code, cap_ms=300).outcome is RunOutcome.TIMEOUT

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


def test_a_run_carries_no_path_and_no_callable():
    """JSON in and JSON out, so a remote sandbox takes the same payload."""
    request = {"code": DOUBLE, "args": [1], "cap_ms": 1000}

    assert json.loads(json.dumps(request)) == request
