from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem


def make_problem(id: str = "i1", **overrides) -> Problem:
    fields = {
        "id": id,
        "title": "Two Sum",
        "title_slug": "two-sum",
        "statement": "Given an array, return ...",
    } | overrides
    return Problem.model_validate(fields)


def test_put_and_get(tmp_path):
    store = ProblemStore(tmp_path)
    problem = make_problem()
    store.put(problem)

    assert store.get("i1") == problem


def test_get_missing_is_none(tmp_path):
    assert ProblemStore(tmp_path).get("nope") is None


def test_put_overwrites(tmp_path):
    """One file per id: the second write of a problem replaces the first."""
    store = ProblemStore(tmp_path)
    store.put(make_problem(title="Two Sum"))
    store.put(make_problem(title="Two Sum II"))

    assert store.get("i1").title == "Two Sum II"
    assert len(store.all()) == 1


def test_all_on_empty_store(tmp_path):
    assert ProblemStore(tmp_path).all() == []
