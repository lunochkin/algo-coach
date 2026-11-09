import io
import json
from typing import Any

import pytest

from algo_coach.runner import child

DOUBLE = "def solve(n):\n    return n * 2\n"


def entered(monkeypatch: pytest.MonkeyPatch, args: list[list[Any]]) -> list[str]:
    """Runs the entry process in this process, with `forked` recording the code
    each child would have run instead of forking."""
    forks: list[str] = []

    def recorded(code: str, _args: list[Any], _cap_ms: int, _repeats: int) -> dict[str, Any]:
        forks.append(code)
        return {"outcome": "returned", "value": "0", "elapsed_ms": 0}

    request = {"code": DOUBLE, "args": args, "cap_ms": 3000, "repeats": None, "stop_early": False}
    monkeypatch.setattr(child, "forked", recorded)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(request)))
    child.main()
    return forks


def test_a_warm_up_child_runs_before_the_first_case(monkeypatch):
    """The first case after a container boots otherwise runs cold under
    gVisor, and its timing is the one a verdict reads."""
    assert entered(monkeypatch, [[1], [2]]) == [child.WARM_UP, DOUBLE, DOUBLE]


def test_no_result_line_reports_the_warm_up(monkeypatch, capsys):
    """The broker reads a line per case, so a line for the warm-up would be
    taken as the first case's result."""
    entered(monkeypatch, [[1], [2]])

    assert len(capsys.readouterr().out.splitlines()) == 2


def test_a_run_with_no_cases_forks_nothing(monkeypatch):
    assert entered(monkeypatch, []) == []
