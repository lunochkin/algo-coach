from datetime import UTC, datetime, timedelta

import pytest
from helpers import make_problem

from algo_coach.log import SittingStore
from algo_coach.problems import ProblemStore
from algo_coach.schema import Sitting
from algo_coach.sitting import Served, serve

BEGAN = datetime.now(UTC) - timedelta(hours=1)


@pytest.fixture
def stores(tmp_path) -> tuple[ProblemStore, SittingStore]:
    problems = ProblemStore(tmp_path)
    problems.put(make_problem("p1", title="Rotated", statement="Given xs ...\n\ndef solve(xs):"))
    return problems, SittingStore(tmp_path)


def a_sitting(**overrides) -> Sitting:
    return Sitting.model_validate(
        {"id": "s0", "user_id": "maks", "problem_id": "p1", "started_at": BEGAN} | overrides
    )


def test_serving_stores_the_sitting_it_returns(stores):
    """The clock is on disk before the statement leaves, so a restart between
    serve and submit loses no start."""
    problems, sittings = stores

    served = serve(problems, sittings, "p1", user_id="maks")

    assert sittings.get(served.sitting.id) == served.sitting
    assert served.sitting.started_at > BEGAN


def test_the_statement_and_title_come_through(stores):
    served = serve(*stores, "p1", user_id="maks")

    assert (served.title, served.statement) == ("Rotated", "Given xs ...\n\ndef solve(xs):")


def test_nothing_the_problem_was_written_from_is_served():
    """A target template or a technique names the form the sitting tests, so a
    field added here that carries one fails this."""
    assert set(Served.model_fields) == {"title", "statement", "sitting"}


def test_a_second_serve_returns_the_running_sitting(stores):
    """A refresh or a second tab reaches the clock already running, rather than
    starting another on the same problem."""
    problems, sittings = stores

    first = serve(problems, sittings, "p1", user_id="maks")
    second = serve(problems, sittings, "p1", user_id="maks")

    assert second.sitting.id == first.sitting.id
    assert len(sittings.all()) == 1


def test_a_paused_sitting_is_returned_paused(stores):
    """Serving resumes nothing: a page reload would otherwise restart a clock
    the user stopped."""
    problems, sittings = stores
    sittings.put(a_sitting(pauses=[{"at": BEGAN + timedelta(minutes=5)}]))

    assert serve(problems, sittings, "p1", user_id="maks").sitting.paused


def test_an_ended_sitting_is_not_reused(stores):
    """Its elapsed time is settled, so a new visit to the problem is a new
    sitting."""
    problems, sittings = stores
    sittings.put(a_sitting(ended_at=BEGAN + timedelta(minutes=30)))

    served = serve(problems, sittings, "p1", user_id="maks")

    assert served.sitting.id != "s0"
    assert len(sittings.all()) == 2


def test_another_user_s_sitting_is_not_reused(stores):
    problems, sittings = stores
    sittings.put(a_sitting(user_id="someone"))

    served = serve(problems, sittings, "p1", user_id="maks")

    assert served.sitting.user_id == "maks" and served.sitting.id != "s0"


def test_an_unknown_problem_is_refused(tmp_path):
    with pytest.raises(ValueError, match="no problem"):
        serve(ProblemStore(tmp_path), SittingStore(tmp_path), "nope", user_id="maks")


def test_a_retired_problem_is_refused(tmp_path):
    """A defective problem was never a fair test, so no clock starts on one."""
    problems = ProblemStore(tmp_path)
    problems.put(make_problem("p1", status="retired", retired_reason="defective"))

    with pytest.raises(ValueError, match="retired"):
        serve(problems, SittingStore(tmp_path), "p1", user_id="maks")
