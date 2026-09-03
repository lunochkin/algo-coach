from datetime import timedelta

import pytest
from helpers import PROVENANCE, T0, make_problem

from algo_coach.mint import user_reading
from algo_coach.problems import derive, with_techniques
from algo_coach.readings import standing_readings
from algo_coach.schema import Solution, SolutionRole, TechniqueReading


def solution(id: str, problem_id: str = "p1", *, role: SolutionRole = SolutionRole.CANONICAL):
    return Solution(
        id=id,
        created_at=T0,
        problem_id=problem_id,
        role=role,
        code="def solve(xs):\n    return sorted(xs)\n",
        **PROVENANCE,
    )


def reading(solution_id: str, techniques: list[str], *, at: int = 0) -> TechniqueReading:
    """A classifier reading, `at` minutes after the one before it."""
    return TechniqueReading(
        id=f"r-{solution_id}-{at}",
        created_at=T0 + timedelta(minutes=at),
        solution_id=solution_id,
        techniques=techniques,
        source="classifier",
        **PROVENANCE,
    )


@pytest.fixture
def problem():
    return make_problem("p1")


def techniques(problem, solutions, readings) -> list[str]:
    return derive([problem], solutions, readings)[problem.id]


def test_the_techniques_are_the_union_over_the_canonicals(problem):
    """Two canonicals of one problem take two approaches, and solving it can
    take either."""
    solutions = [solution("s1"), solution("s2")]
    readings = [reading("s1", ["sorting"]), reading("s2", ["hashing", "sorting"])]

    assert techniques(problem, solutions, readings) == ["hashing", "sorting"]


def test_the_reference_is_excluded(problem):
    """It is written from the statement alone, so counting it would credit the
    naive approach the canonical's form replaces."""
    solutions = [solution("s1"), solution("s2", role=SolutionRole.REFERENCE)]
    readings = [reading("s1", ["sorting"]), reading("s2", ["recursion"])]

    assert techniques(problem, solutions, readings) == ["sorting"]


def test_a_canonical_nothing_read_contributes_nothing(problem):
    """The derivation has no input for it, which is not a verdict that it uses
    no technique."""
    solutions = [solution("s1"), solution("s2")]

    assert techniques(problem, solutions, [reading("s1", ["sorting"])]) == ["sorting"]


def test_the_user_reading_stands_over_a_later_machine_one(problem):
    """A hand record adjudicates, and the machine's is kept and scored rather
    than promoted."""
    readings = [
        user_reading("s1", ["greedy"]),
        reading("s1", ["sorting"], at=60),
    ]

    assert techniques(problem, [solution("s1")], readings) == ["greedy"]


def test_the_latest_machine_reading_stands(problem):
    """Re-derivation is the normal path, so a second reading of one solution
    supersedes the first."""
    readings = [reading("s1", ["sorting"]), reading("s1", ["greedy"], at=10)]

    assert techniques(problem, [solution("s1")], readings) == ["greedy"]


def test_a_re_reading_that_named_nothing_narrows_the_view(problem):
    """An empty reading is a verdict about the code, so what it supersedes
    stops being counted."""
    readings = [reading("s1", ["sorting"]), reading("s1", [], at=10)]

    assert techniques(problem, [solution("s1")], readings) == []


def test_another_problem_s_canonicals_are_not_counted(problem):
    solutions = [solution("s1"), solution("s2", problem_id="p2")]
    readings = [reading("s1", ["sorting"]), reading("s2", ["greedy"])]

    assert techniques(problem, solutions, readings) == ["sorting"]


def test_a_problem_carries_the_view_rather_than_what_its_record_stores():
    """Stored truth would drift: a canonical added later widens the union, and
    nothing revises the record it was read off."""
    stale = make_problem("p1", techniques=["dynamic-programming"])

    (derived,) = with_techniques([stale], [solution("s1")], [reading("s1", ["sorting"])])

    assert derived.techniques == ["sorting"]
    assert derived.id == stale.id


def test_the_order_is_fixed(problem):
    """A claim's prompt is rendered from these, and the digest is taken over
    that text. Drawn from a set the order would move with the hash seed."""
    solutions = [solution("s1"), solution("s2")]
    readings = [reading("s1", ["sorting", "greedy"]), reading("s2", ["hashing"])]

    assert techniques(problem, solutions, readings) == ["greedy", "hashing", "sorting"]


def test_standing_is_keyed_by_solution(problem):
    """The resolver alone: one record per solution, the user's over the
    machine's."""
    readings = [reading("s1", ["sorting"]), user_reading("s1", ["greedy"]), reading("s2", [])]

    standing = standing_readings(readings)

    assert {id: one.techniques for id, one in standing.items()} == {"s1": ["greedy"], "s2": []}
