from datetime import UTC, datetime, timedelta

from algo_coach.schema import Attempt
from algo_coach.sitting import carry

T0 = datetime(2026, 10, 1, 9, tzinfo=UTC)


def attempt(id: str, *, minutes: int, solved: bool, code: str | None = "x = 1") -> Attempt:
    return Attempt(
        id=id,
        user_id="u-4f9c2a",
        problem_id="p1",
        sitting_id=f"s-{id}",
        finished_at=T0 + timedelta(minutes=minutes),
        solved=solved,
        code=code,
    )


def test_an_unsolved_last_attempt_is_carried():
    """Reopening a half-solved problem continues it."""
    one = carry([attempt("a1", minutes=0, solved=False, code="wip")], run_started_at=None)

    assert (one.code, one.at) == ("wip", T0)


def test_a_solve_is_never_carried():
    """Prefilling an answer turns a re-solve into reading it."""
    one = carry(
        [attempt("a1", minutes=0, solved=False), attempt("a2", minutes=5, solved=True)],
        run_started_at=None,
    )

    assert one.code is None
    assert (one.solved_at, one.solved_sitting_id) == (T0 + timedelta(minutes=5), "s-a2")


def test_the_last_solve_s_code_is_offered_for_the_restore_press():
    """The page restores it only on the user's press."""
    one = carry([attempt("a1", minutes=0, solved=True, code="answer")], run_started_at=None)

    assert (one.code, one.solved_code) == (None, "answer")


def test_work_after_a_solve_is_carried():
    """A wrong attempt after the solve is new work in progress."""
    one = carry(
        [attempt("a1", minutes=0, solved=True), attempt("a2", minutes=5, solved=False, code="new")],
        run_started_at=None,
    )

    assert one.code == "new"


def test_code_from_before_the_run_is_not_carried():
    """The run measures solving from its start."""
    one = carry([attempt("a1", minutes=0, solved=False)], run_started_at=T0 + timedelta(minutes=1))

    assert one.code is None and one.run_started_at == T0 + timedelta(minutes=1)


def test_code_from_within_the_run_is_carried():
    one = carry([attempt("a1", minutes=5, solved=False, code="in")], run_started_at=T0)

    assert one.code == "in"


def test_nothing_attempted_carries_nothing():
    one = carry([], run_started_at=None)

    assert (one.code, one.solved_at) == (None, None)
