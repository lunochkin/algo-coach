from datetime import UTC, datetime, timedelta

from algo_coach.board import candidates
from algo_coach.schema import Attempt, Problem

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def make_problem(id: str, techniques: list[str]) -> Problem:
    return Problem(
        id=id,
        title=id,
        title_slug=id,
        statement="Given an array, return ...",
        techniques=techniques,
    )


def make_attempt(
    id: str, problem_id: str, *, finished_at: datetime = T0, solved: bool = True
) -> Attempt:
    return Attempt(
        id=id,
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=solved,
    )


GREEDY = make_problem("greedy-one", ["greedy"])
TRIE = make_problem("trie-one", ["trie"])


def test_only_problems_carrying_the_technique_are_offered():
    rows = candidates("greedy", [GREEDY, TRIE], [])

    assert [row.problem.id for row in rows] == ["greedy-one"]


def test_no_problem_carries_it():
    assert candidates("binary-search", [GREEDY, TRIE], []) == []


def test_membership_is_the_problems_tags_not_its_attempts():
    """Selection asks what a problem could exercise. A claim describing one
    past solution must not remove it from what it is tagged for."""
    rows = candidates("greedy", [GREEDY], [make_attempt("a1", "greedy-one")])

    assert [row.problem.id for row in rows] == ["greedy-one"]


def test_a_never_attempted_problem_ranks_first():
    """Nothing has been retrieved yet, so nothing has decayed."""
    fresh = make_problem("greedy-two", ["greedy"])
    rows = candidates("greedy", [GREEDY, fresh], [make_attempt("a1", "greedy-one")])

    assert [row.problem.id for row in rows] == ["greedy-two", "greedy-one"]
    assert rows[0].last_attempt_at is None
    assert rows[0].attempt_count == 0


def test_the_least_recently_attempted_comes_first():
    old = make_problem("greedy-old", ["greedy"])
    rows = candidates(
        "greedy",
        [GREEDY, old],
        [
            make_attempt("a1", "greedy-one", finished_at=T0 + timedelta(days=30)),
            make_attempt("a2", "greedy-old", finished_at=T0),
        ],
    )

    assert [row.problem.id for row in rows] == ["greedy-old", "greedy-one"]


def test_recency_is_the_latest_attempt_on_the_problem():
    rows = candidates(
        "greedy",
        [GREEDY],
        [
            make_attempt("a1", "greedy-one", finished_at=T0),
            make_attempt("a2", "greedy-one", finished_at=T0 + timedelta(days=5)),
        ],
    )

    assert rows[0].last_attempt_at == T0 + timedelta(days=5)
    assert rows[0].attempt_count == 2


def test_the_lower_solve_rate_breaks_a_tie_on_staleness():
    """Same day, so the one that went worse is the one worth redoing."""
    shaky = make_problem("greedy-shaky", ["greedy"])
    rows = candidates(
        "greedy",
        [GREEDY, shaky],
        [
            make_attempt("a1", "greedy-one", solved=True),
            make_attempt("a2", "greedy-shaky", solved=True),
            make_attempt("a3", "greedy-shaky", solved=False),
        ],
    )

    assert [row.problem.id for row in rows] == ["greedy-shaky", "greedy-one"]


def test_problem_id_breaks_a_tie_on_both():
    """Two renders of the same log offer the same order."""
    other = make_problem("greedy-aaa", ["greedy"])
    rows = candidates(
        "greedy",
        [GREEDY, other],
        [make_attempt("a1", "greedy-one"), make_attempt("a2", "greedy-aaa")],
    )

    assert [row.problem.id for row in rows] == ["greedy-aaa", "greedy-one"]


def test_a_row_counts_only_its_own_problems_attempts():
    rows = candidates(
        "greedy",
        [GREEDY],
        [
            make_attempt("a1", "greedy-one", solved=False),
            make_attempt("a2", "trie-one"),
        ],
    )

    assert (rows[0].attempt_count, rows[0].solved_count) == (1, 0)


def test_a_problem_carrying_no_technique_is_offered_for_nothing():
    """Selection is per technique, so a problem naming none is reachable from
    no row."""
    unmapped = make_problem("db-one", [])

    assert candidates("greedy", [unmapped], []) == []
