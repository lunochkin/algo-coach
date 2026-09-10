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
    """`README.md`: `techniques` is derived from the solution claims, and a record
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


def test_retiring_moves_the_status_and_names_the_reason(tmp_path):
    """A defective problem leaves serving, and a bare status would leave every
    reader guessing why."""
    store = ProblemStore(tmp_path)
    store.put(make_problem())

    retired = store.retire("i1", RetirementReason.DEFECTIVE)

    assert store.get("i1") == retired
    assert (retired.status, retired.retired_reason) == (
        ProblemStatus.RETIRED,
        RetirementReason.DEFECTIVE,
    )
    assert not retired.served


def test_retiring_moves_nothing_but_the_status(tmp_path):
    """The attempts made against the problem stay with the record they were made
    against."""
    store = ProblemStore(tmp_path)
    store.put(make_problem())
    before = store.get("i1").model_dump(exclude={"status", "retired_reason"})

    store.retire("i1", RetirementReason.DEFECTIVE)

    assert store.get("i1").model_dump(exclude={"status", "retired_reason"}) == before


def test_retiring_a_retired_problem_changes_nothing(tmp_path):
    """A sitting asks about each attempt in turn, so a second mark on one
    problem is the loop repeating itself."""
    store = ProblemStore(tmp_path)
    store.put(make_problem())
    first = store.retire("i1", RetirementReason.DEFECTIVE)

    assert store.retire("i1", RetirementReason.DEFECTIVE) == first
    assert len(store.all()) == 1


def test_retiring_an_unknown_problem_is_refused(tmp_path):
    with pytest.raises(ValueError, match="no problem"):
        ProblemStore(tmp_path).retire("nope", RetirementReason.DEFECTIVE)
