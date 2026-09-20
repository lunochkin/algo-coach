from datetime import UTC, datetime

import pytest
from helpers import PROVENANCE, stored_problem

from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.mint import attempt_verification, case
from algo_coach.schema import (
    Attempt,
    CaseOutcome,
    CaseResult,
    Execution,
    FailureMode,
    Sitting,
)
from algo_coach.sitting import Missing, Refused, label, modes

USER = "u-4f9c2a"


def run(*outcomes: CaseOutcome, cases: list[str] | None = None) -> Execution:
    named = cases or [f"c{position}" for position, _ in enumerate(outcomes)]
    return Execution(
        cap_ms=2_000,
        runner="subprocess/3.14",
        results=[
            CaseResult(
                case_id=case_id,
                outcome=outcome,
                elapsed_ms=1,
                error="ZeroDivisionError" if outcome is CaseOutcome.CRASHED else None,
            )
            for case_id, outcome in zip(named, outcomes, strict=True)
        ],
    )


@pytest.fixture
def cases(database) -> list[str]:
    """The problem, its two cases and the sitting this module's records name."""
    stored_problem(database, "p1")
    SittingStore(database).put(
        Sitting(
            id="s1",
            user_id=USER,
            problem_id="p1",
            started_at=datetime(2026, 9, 10, 8, tzinfo=UTC),
        )
    )
    log = CaseLog(database)
    stored = [case("p1", [one], one, provenance=PROVENANCE) for one in (0, 1)]
    for one in stored:
        log.append(one)
    return [one.id for one in stored]


@pytest.fixture
def log(database, cases) -> AttemptLog:
    one = AttemptLog(database)
    judged = {
        "passed": run(CaseOutcome.PASSED, CaseOutcome.PASSED, cases=cases),
        "wrong": run(CaseOutcome.PASSED, CaseOutcome.WRONG, cases=cases),
        "crashed": run(CaseOutcome.CRASHED, CaseOutcome.CRASHED, cases=cases),
    }
    for attempt_id, judgement in judged.items():
        one.append_attempt(
            Attempt(
                id=attempt_id,
                user_id=USER,
                problem_id="p1",
                sitting_id="s1",
                finished_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                solved=judgement.verified,
            )
        )
        one.append_verification(attempt_verification(attempt_id, judgement))
    return one


def an_attempt(*, solved: bool) -> Attempt:
    return Attempt(
        id="a",
        user_id=USER,
        problem_id="p1",
        sitting_id="s1",
        finished_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
        solved=solved,
    )


def test_the_modes_split_by_the_verdict():
    """A solved attempt failed at nothing, so the three modes that name a
    failure are not open to it."""
    passed = run(CaseOutcome.PASSED)
    wrong = run(CaseOutcome.PASSED, CaseOutcome.WRONG)

    assert modes(an_attempt(solved=True), attempt_verification("a", passed)) == [
        FailureMode.SPEED,
        FailureMode.NONE,
    ]
    assert modes(an_attempt(solved=False), attempt_verification("a", wrong)) == [
        FailureMode.GAP,
        FailureMode.RUST,
        FailureMode.SYNTAX,
    ]


def test_an_attempt_that_crashed_on_every_case_is_asked_nothing():
    """The code reached no answer, so no mode is more than a guess."""
    crashed = run(CaseOutcome.CRASHED, CaseOutcome.CRASHED)

    assert modes(an_attempt(solved=False), attempt_verification("a", crashed)) == []


def test_an_attempt_no_run_judged_takes_the_verdict_s_own_split():
    """An attempt carries `solved` itself, so a missing verification narrows
    nothing rather than closing every mode."""
    assert modes(an_attempt(solved=False), None) == [
        FailureMode.GAP,
        FailureMode.RUST,
        FailureMode.SYNTAX,
    ]


def test_a_label_is_stored_against_the_attempt(log):
    written = label(log, "wrong", FailureMode.RUST, user_id=USER)

    assert (written.attempt_id, written.mode) == ("wrong", FailureMode.RUST)
    assert log.self_labels(USER) == [written]


def test_a_mode_the_verdict_leaves_closed_is_refused(log):
    """A label contradicting the verdict would answer a question the
    verification already settled."""
    with pytest.raises(Refused):
        label(log, "passed", FailureMode.GAP, user_id=USER)

    with pytest.raises(Refused):
        label(log, "wrong", FailureMode.SPEED, user_id=USER)

    with pytest.raises(Refused):
        label(log, "crashed", FailureMode.SYNTAX, user_id=USER)

    assert log.self_labels(USER) == []


def test_a_second_label_appends(log):
    """The log is append-only, and the latest label wins on read."""
    first = label(log, "wrong", FailureMode.GAP, user_id=USER)
    second = label(log, "wrong", FailureMode.RUST, user_id=USER)

    assert log.self_labels(USER) == [first, second]


def test_another_user_s_attempt_is_missing(log):
    with pytest.raises(Missing):
        label(log, "wrong", FailureMode.RUST, user_id="u-b71e03")
