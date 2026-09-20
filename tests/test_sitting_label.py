from datetime import UTC, datetime

import pytest
from helpers import stored_problem

from algo_coach.log import AttemptLog, SittingStore
from algo_coach.schema import Attempt, FailureMode, Sitting
from algo_coach.sitting import Missing, Refused, label, modes

USER = "u-4f9c2a"


@pytest.fixture(autouse=True)
def referenced(database):
    """The problem and the sitting this module's attempts name."""
    stored_problem(database, "p1")
    SittingStore(database).put(
        Sitting(
            id="s1",
            user_id=USER,
            problem_id="p1",
            started_at=datetime(2026, 9, 10, 8, tzinfo=UTC),
        )
    )


@pytest.fixture
def log(database) -> AttemptLog:
    one = AttemptLog(database)
    for attempt_id, solved in (("a1", True), ("a2", False)):
        one.append_attempt(
            Attempt(
                id=attempt_id,
                user_id=USER,
                problem_id="p1",
                sitting_id="s1",
                finished_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
                solved=solved,
            )
        )
    return one


def test_the_modes_split_by_the_attempt_s_verdict():
    """A solved attempt failed at nothing, so the three modes that name a
    failure are not open to it."""
    assert modes(solved=True) == (FailureMode.SPEED, FailureMode.NONE)
    assert modes(solved=False) == (FailureMode.GAP, FailureMode.RUST, FailureMode.SYNTAX)


def test_a_label_is_stored_against_the_attempt(log):
    written = label(log, "a2", FailureMode.RUST, user_id=USER)

    assert (written.attempt_id, written.mode) == ("a2", FailureMode.RUST)
    assert log.self_labels(USER) == [written]


def test_a_mode_the_verdict_leaves_closed_is_refused(log):
    """A label contradicting the verdict would answer a question the
    verification already settled."""
    with pytest.raises(Refused):
        label(log, "a1", FailureMode.GAP, user_id=USER)

    with pytest.raises(Refused):
        label(log, "a2", FailureMode.SPEED, user_id=USER)

    assert log.self_labels(USER) == []


def test_a_second_label_appends(log):
    """The log is append-only, and the latest label wins on read."""
    first = label(log, "a2", FailureMode.GAP, user_id=USER)
    second = label(log, "a2", FailureMode.RUST, user_id=USER)

    assert log.self_labels(USER) == [first, second]


def test_another_user_s_attempt_is_missing(log):
    with pytest.raises(Missing):
        label(log, "a2", FailureMode.RUST, user_id="u-b71e03")
