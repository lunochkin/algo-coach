from datetime import UTC, datetime, timedelta

from algo_coach.log import appeared
from algo_coach.schema import Attempt, AttemptOrigin

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def make_attempt(id: str, *, problem_id: str = "p1", finished_at: datetime = T0) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=True,
        origin=AttemptOrigin.PUSH,
    )


def test_nothing_pushed_means_nothing_appeared():
    log = [make_attempt("a1")]

    assert appeared(log, problem_id="p1", known={"a1"}) == []


def test_an_attempt_the_snapshot_did_not_hold_appeared():
    fresh = make_attempt("a2")

    assert appeared([make_attempt("a1"), fresh], problem_id="p1", known={"a1"}) == [fresh]


def test_an_attempt_on_another_problem_is_not_this_drills():
    """Pushed in the same batch, but not what was just solved."""
    other = make_attempt("a2", problem_id="p2")

    assert appeared([other], problem_id="p1", known=set()) == []


def test_the_first_attempt_on_a_problem_appears():
    fresh = make_attempt("a1")

    assert appeared([fresh], problem_id="p1", known=set()) == [fresh]


def test_a_sitting_is_returned_in_the_order_it_happened():
    """The push may land them in any order; the prompts follow the clock."""
    second = make_attempt("a2", finished_at=T0 + timedelta(minutes=5))
    first = make_attempt("a1", finished_at=T0)

    assert appeared([second, first], problem_id="p1", known=set()) == [first, second]


def test_a_tie_on_the_clock_is_broken_by_id():
    a = make_attempt("a1")
    b = make_attempt("a2")

    assert appeared([b, a], problem_id="p1", known=set()) == [a, b]


def test_a_backfilled_attempt_pushed_mid_drill_counts():
    """New to the log is the only question: the loop asks about what it can
    now see and could not before."""
    old = make_attempt("a9", finished_at=T0 - timedelta(days=400))

    assert appeared([old], problem_id="p1", known=set()) == [old]


def test_an_empty_log():
    assert appeared([], problem_id="p1", known=set()) == []
