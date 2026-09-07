import pytest
from helpers import GENERATED

from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem, ProblemStatus, RetirementReason


def make_problem(id: str = "i1", **overrides) -> Problem:
    fields = (
        {
            "id": id,
            "title": "Two Sum",
            "statement": "Given an array, return ...",
        }
        | GENERATED
        | overrides
    )
    return Problem.model_validate(fields)


def test_put_and_get(tmp_path):
    store = ProblemStore(tmp_path)
    problem = make_problem()
    store.put(problem)

    assert store.get("i1") == problem


def test_get_missing_is_none(tmp_path):
    assert ProblemStore(tmp_path).get("nope") is None


def test_a_stored_problem_is_not_rewritten(tmp_path):
    """`corpus.md`: a statement that says the wrong thing is retired and a new
    problem written, so the attempts stay with what they were made against."""
    store = ProblemStore(tmp_path)
    store.put(make_problem(title="Two Sum"))

    with pytest.raises(ValueError, match="only its status moves"):
        store.put(make_problem(title="Two Sum II"))
    assert store.get("i1").title == "Two Sum"


def test_only_the_status_of_a_stored_problem_moves(tmp_path):
    """Created, then retired: the one write an existing problem takes."""
    store = ProblemStore(tmp_path)
    store.put(make_problem())

    store.put(make_problem(status=ProblemStatus.RETIRED, retired_reason=RetirementReason.DEFECTIVE))

    assert store.get("i1").status is ProblemStatus.RETIRED
    assert len(store.all()) == 1


def test_a_problem_carrying_its_view_is_refused(tmp_path):
    """`README.md`: `techniques` is derived from the readings, and a record
    stored with it would be truth nothing re-derives."""
    with pytest.raises(ValueError, match="carries a view"):
        ProblemStore(tmp_path).put(make_problem(techniques=["greedy"]))


def test_writing_the_same_problem_again_is_allowed(tmp_path):
    """A run that died between two writes of one landing may write it again."""
    store = ProblemStore(tmp_path)
    store.put(make_problem())
    store.put(make_problem())

    assert len(store.all()) == 1


def test_all_on_empty_store(tmp_path):
    assert ProblemStore(tmp_path).all() == []
