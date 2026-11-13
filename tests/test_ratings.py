from datetime import timedelta

import pytest
from helpers import PROVENANCE_FIELDS, T0, make_problem
from pydantic import ValidationError

from algo_coach.mint import user_rating
from algo_coach.problems import ProblemStore
from algo_coach.ratings import RatingLog, with_standing_difficulty
from algo_coach.schema import DifficultyRating, ProblemDifficulty
from algo_coach.solution_claims import load_problem, load_problems

EASY, MEDIUM, HARD = ProblemDifficulty.EASY, ProblemDifficulty.MEDIUM, ProblemDifficulty.HARD


def rating(difficulty, *, source="user", at=0, problem_id="p1") -> DifficultyRating:
    machine = PROVENANCE_FIELDS if source == "classifier" else {}
    return DifficultyRating(
        id=f"r-{source}-{at}",
        created_at=T0 + timedelta(minutes=at),
        problem_id=problem_id,
        difficulty=difficulty,
        source=source,
        **machine,
    )


def standing(problem, ratings) -> ProblemDifficulty | None:
    (rated,) = with_standing_difficulty([problem], ratings)
    return rated.difficulty


def test_an_unrated_problem_keeps_the_generators_label():
    assert standing(make_problem(difficulty=EASY), []) is EASY


def test_the_latest_rating_stands():
    """A rating is superseded by appending another, never by rewriting one."""
    ratings = [rating(HARD, at=0), rating(MEDIUM, at=1)]

    assert standing(make_problem(difficulty=EASY), ratings) is MEDIUM


def test_the_users_rating_stands_over_a_later_machine_one():
    ratings = [rating(MEDIUM, at=0), rating(HARD, source="classifier", at=5)]

    assert standing(make_problem(difficulty=EASY), ratings) is MEDIUM


def test_a_rating_of_another_problem_moves_nothing():
    ratings = [rating(HARD, problem_id="p2")]

    assert standing(make_problem(difficulty=EASY), ratings) is EASY


def test_a_machine_rating_carries_its_provenance():
    with pytest.raises(ValidationError):
        DifficultyRating(
            id="r1", created_at=T0, problem_id="p1", difficulty=EASY, source="classifier"
        )


def test_the_loaders_serve_the_standing_difficulty(database):
    """Every reader of a label loads through these, so a rating reaches the
    badge, the listing's filter and the selector at once."""
    ProblemStore(database).put(make_problem(difficulty=EASY))
    RatingLog(database).append(user_rating("p1", HARD))

    (every,) = load_problems(database)
    one = load_problem(database, "p1")

    assert (every.difficulty, one.difficulty if one else None) == (HARD, HARD)
    assert ProblemStore(database).get("p1").difficulty is EASY
