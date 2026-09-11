from datetime import UTC, datetime, timedelta

import pytest
from helpers import make_problem

from algo_coach.log import SittingStore
from algo_coach.problems import ProblemStore
from algo_coach.schema import RetirementReason, Sitting
from algo_coach.sitting import Missing, Refused, Served, get, serve

BEGAN = datetime.now(UTC) - timedelta(hours=1)


@pytest.fixture
def stores(tmp_path) -> tuple[ProblemStore, SittingStore]:
    problems = ProblemStore(tmp_path)
    problems.put(make_problem("p1", title="Rotated", statement="Given xs ...\n\ndef solve(xs):"))
    return problems, SittingStore(tmp_path)


def a_sitting(**overrides) -> Sitting:
    return Sitting.model_validate(
        {"id": "s0", "user_id": "u-4f9c2a", "problem_id": "p1", "started_at": BEGAN} | overrides
    )


def test_serving_stores_the_sitting_it_returns(stores):
    """The clock is on disk before the statement leaves, so a restart between
    serve and submit loses no start."""
    problems, sittings = stores

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert sittings.get(served.sitting.id) == served.sitting
    assert served.sitting.started_at > BEGAN


def test_the_statement_and_title_come_through(stores):
    served = serve(*stores, "p1", user_id="u-4f9c2a")

    assert (served.title, served.statement) == ("Rotated", "Given xs ...")


def test_the_signature_is_split_from_the_prose(stores):
    """A parameter like `max_cost` read as markdown is an emphasis, so the page
    gets the line apart and shows it as code."""
    assert serve(*stores, "p1", user_id="u-4f9c2a").signature == "def solve(xs):"


def test_a_signature_in_a_fenced_block_is_split_with_its_fence(tmp_path):
    problems = ProblemStore(tmp_path)
    statement = (
        "Find the centre.\n\n```python\ndef solve(n: int, edges: list[list[int]]) -> int:\n```\n"
    )
    problems.put(make_problem("p1", statement=statement))

    served = serve(problems, SittingStore(tmp_path), "p1", user_id="u-4f9c2a")

    assert (served.statement, served.signature) == (
        "Find the centre.",
        "def solve(n: int, edges: list[list[int]]) -> int:",
    )


@pytest.mark.parametrize(
    "statement",
    [
        "Given an array, return its sum.",
        "Write `def solve(xs):` returning the sum.",
        "def solve(xs) is mentioned first.\n\nThen the prose goes on.",
    ],
)
def test_a_statement_not_ending_on_the_line_is_all_prose(tmp_path, statement):
    """A mention of the call inside a sentence is not the declaration."""
    problems = ProblemStore(tmp_path)
    problems.put(make_problem("p1", statement=statement))

    served = serve(problems, SittingStore(tmp_path), "p1", user_id="u-4f9c2a")

    assert (served.statement, served.signature) == (statement, None)


def test_nothing_the_problem_was_written_from_is_served():
    """A target template or a technique names the form the sitting tests, so a
    field added here that carries one fails this."""
    assert set(Served.model_fields) == {"title", "statement", "signature", "sitting", "elapsed_sec"}


def test_a_second_serve_returns_the_running_sitting(stores):
    """A refresh or a second tab reaches the clock already running, rather than
    starting another on the same problem."""
    problems, sittings = stores

    first = serve(problems, sittings, "p1", user_id="u-4f9c2a")
    second = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert second.sitting.id == first.sitting.id
    assert len(sittings.all()) == 1


def test_a_paused_sitting_is_returned_paused(stores):
    """Serving resumes nothing: a page reload would otherwise restart a clock
    the user stopped."""
    problems, sittings = stores
    sittings.put(a_sitting(pauses=[{"at": BEGAN + timedelta(minutes=5)}]))

    assert serve(problems, sittings, "p1", user_id="u-4f9c2a").sitting.paused


def test_an_ended_sitting_is_not_reused(stores):
    """Its elapsed time is settled, so a new visit to the problem is a new
    sitting."""
    problems, sittings = stores
    sittings.put(a_sitting(ended_at=BEGAN + timedelta(minutes=30)))

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert served.sitting.id != "s0"
    assert len(sittings.all()) == 2


def test_another_user_s_sitting_is_not_reused(stores):
    problems, sittings = stores
    sittings.put(a_sitting(user_id="u-b71e03"))

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert served.sitting.user_id == "u-4f9c2a" and served.sitting.id != "s0"


def test_an_unknown_problem_is_refused(tmp_path):
    with pytest.raises(Missing, match="no problem"):
        serve(ProblemStore(tmp_path), SittingStore(tmp_path), "nope", user_id="u-4f9c2a")


def test_a_retired_problem_is_refused(tmp_path):
    """A defective problem was never a fair test, so no clock starts on one."""
    problems = ProblemStore(tmp_path)
    problems.put(make_problem("p1", status="retired", retired_reason="defective"))

    with pytest.raises(Refused, match="retired"):
        serve(problems, SittingStore(tmp_path), "p1", user_id="u-4f9c2a")


def test_a_sitting_is_read_back_as_it_was_served(stores):
    """The sitting's page has its own URL, and a reload there needs the
    statement without starting a clock."""
    problems, sittings = stores
    at = datetime.now(UTC)
    served = serve(problems, sittings, "p1", user_id="u-4f9c2a", now=at)

    assert get(problems, sittings, served.sitting.id, user_id="u-4f9c2a", now=at) == served
    assert len(sittings.all()) == 1


def test_an_ended_sitting_is_still_read(stores):
    """The claim is asked once the sitting ends, on the same page."""
    problems, sittings = stores
    sittings.put(a_sitting(ended_at=BEGAN + timedelta(minutes=30)))

    assert get(problems, sittings, "s0", user_id="u-4f9c2a").sitting.ended_at is not None


def test_a_sitting_on_a_since_retired_problem_is_still_read(stores):
    """The statement was served before the retirement, and the attempts stay
    with it."""
    problems, sittings = stores
    sittings.put(a_sitting())
    problems.retire("p1", RetirementReason.DEFECTIVE)

    assert get(problems, sittings, "s0", user_id="u-4f9c2a").title == "Rotated"


def test_another_user_s_sitting_reads_as_missing(stores):
    problems, sittings = stores
    sittings.put(a_sitting(user_id="u-b71e03"))

    with pytest.raises(Missing, match="no sitting"):
        get(problems, sittings, "s0", user_id="u-4f9c2a")


def test_the_elapsed_time_is_read_on_the_engine_s_clock(stores):
    """A page counting on from the browser's clock would show a duration no
    attempt carries."""
    problems, sittings = stores
    sittings.put(
        a_sitting(
            pauses=[{"at": BEGAN + timedelta(minutes=10), "until": BEGAN + timedelta(minutes=40)}]
        )
    )

    served = get(problems, sittings, "s0", user_id="u-4f9c2a", now=BEGAN + timedelta(hours=1))

    assert served.elapsed_sec == 30 * 60
