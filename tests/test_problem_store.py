from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem, ProblemOwner


def make_problem(id: str = "i1", external_id: str = "e1", **overrides) -> Problem:
    fields = {
        "id": id,
        "external_id": external_id,
        "user_id": "u1",
        "owner": ProblemOwner.USER,
        "title": "Two Sum",
        "title_slug": "two-sum",
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
    """A mutable cache: the second push of a problem replaces the first."""
    store = ProblemStore(tmp_path)
    store.put(make_problem(title="Two Sum"))
    store.put(make_problem(title="Two Sum II"))

    assert store.get("i1").title == "Two Sum II"
    assert len(store.all()) == 1


def test_by_external_scopes_to_the_user(tmp_path):
    store = ProblemStore(tmp_path)
    store.put(make_problem(id="i1", external_id="e1", user_id="u1"))
    store.put(make_problem(id="i2", external_id="e1", user_id="u2"))

    assert store.by_external("u1", "e1").id == "i1"
    assert store.by_external("u2", "e1").id == "i2"
    assert store.by_external("u3", "e1") is None


def test_all_on_empty_store(tmp_path):
    assert ProblemStore(tmp_path).all() == []
