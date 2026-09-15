import json
from typing import Any

import httpx
import pytest

from algo_coach.runner import CaseRun, RunOutcome, run, runner
from algo_coach.runner.execution import LOCAL_RUNNER, RunnerError
from algo_coach.runner.remote import BROKER, RUNNER, request

DOUBLE = "def solve(n):\n    return n * 2\n"


class Answered:
    """Answers as the broker would, and keeps every request it was sent."""

    def __init__(self, cases: list[dict[str, Any]] | None = None, status: int = 200) -> None:
        self.cases = cases if cases is not None else []
        self.status = status
        self.sent: list[httpx.Request] = []

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def __call__(self, sent: httpx.Request) -> httpx.Response:
        self.sent.append(sent)
        return httpx.Response(self.status, json={"cases": self.cases})


@pytest.fixture
def brokered(monkeypatch: pytest.MonkeyPatch):
    """The broker named, and its transport answering in place of a container."""

    def named(answered: Answered) -> Answered:
        monkeypatch.setenv(BROKER, "http://broker:8001")
        monkeypatch.setattr("algo_coach.runner.remote.TRANSPORT", answered.transport())
        return answered

    return named


def returned(value: object, elapsed_ms: int = 1) -> dict[str, Any]:
    return {"outcome": "returned", "value": json.dumps(value), "elapsed_ms": elapsed_ms}


def test_a_request_carries_the_code_the_arguments_and_the_cap_and_nothing_else():
    """`corpus.md` keeps the comparison above the runner, and a sandbox told
    what a case expects can be made to agree with it."""
    body = request(DOUBLE, [[1], [2]], 2000, [1, 1], False)

    assert set(body) == {"code", "args", "cap_ms", "repeats", "stop_early"}
    assert "expected" not in json.dumps(body)


def test_a_run_reaches_the_broker_where_one_is_named(brokered):
    answered = brokered(Answered([returned(2), returned(4)]))

    results = run(DOUBLE, [[1], [2]], cap_ms=2000)

    assert results == [
        CaseRun(RunOutcome.RETURNED, 2, elapsed_ms=1),
        CaseRun(RunOutcome.RETURNED, 4, elapsed_ms=1),
    ]
    (sent,) = answered.sent
    assert sent.url.path == "/run"
    assert json.loads(sent.content) == request(DOUBLE, [[1], [2]], 2000, [1, 1], False)


def test_a_case_the_broker_reports_as_crashed_carries_what_raised(brokered):
    crashed = {"outcome": "crashed", "value": None, "elapsed_ms": 3, "error": "ValueError: no"}
    brokered(Answered([crashed]))

    (result,) = run(DOUBLE, [[1]], cap_ms=2000)

    assert result == CaseRun(RunOutcome.CRASHED, None, elapsed_ms=3, error="ValueError: no")


def test_a_broker_that_answers_no_result_is_the_runner_s_own_fault(brokered):
    """A runner fault is raised, never recorded: a stored `CRASHED` would
    reject a sound draft over the runner's defect."""
    brokered(Answered(status=503))

    with pytest.raises(RunnerError, match="503"):
        run(DOUBLE, [[1]], cap_ms=2000)


def test_a_broker_nothing_answers_at_is_the_runner_s_own_fault(monkeypatch):
    monkeypatch.setenv(BROKER, "http://broker:8001")
    monkeypatch.setattr(
        "algo_coach.runner.remote.TRANSPORT",
        httpx.MockTransport(lambda _: (_ for _ in ()).throw(httpx.ConnectError("refused"))),
    )

    with pytest.raises(RunnerError, match="answered nothing"):
        run(DOUBLE, [[1]], cap_ms=2000)


def test_code_reaching_no_solve_is_decided_without_a_container(brokered):
    """The tree says the code cannot reach `solve`, so no run is paid for."""
    answered = brokered(Answered())

    results = run("x = 1\n", [[1], [2]], cap_ms=2000)

    assert [each.outcome for each in results] == [RunOutcome.CRASHED, RunOutcome.CRASHED]
    assert answered.sent == []


def test_the_runner_names_the_backend_that_answered(monkeypatch):
    """Two runs are comparable only within one runner, and a container and a
    local subprocess decide a timeout differently."""
    assert runner() == LOCAL_RUNNER

    monkeypatch.setenv(BROKER, "http://broker:8001")

    assert runner() == RUNNER
