from datetime import UTC, datetime, timedelta

import pytest
from helpers import make_problem

from algo_coach.log import SittingStore
from algo_coach.problems import ProblemStore
from algo_coach.schema import RetirementReason, Sitting
from algo_coach.sitting import Missing, Refused, Served, begin, get, serve

BEGAN = datetime.now(UTC) - timedelta(hours=1)


@pytest.fixture
def stores(database) -> tuple[ProblemStore, SittingStore]:
    problems = ProblemStore(database)
    problems.put(make_problem("p1", title="Rotated", statement="Given xs ...\n\ndef solve(xs):"))
    return problems, SittingStore(database)


def a_sitting(**overrides) -> Sitting:
    return Sitting.model_validate(
        {
            "id": "s0",
            "user_id": "u-4f9c2a",
            "problem_id": "p1",
            "started_at": BEGAN,
            "clock_started_at": BEGAN,
            # still running an hour on, so the loop has been touching it: an
            # untouched sitting ends at the bound `log.md` gives
            "last_active_at": datetime.now(UTC),
        }
        | overrides
    )


def test_serving_mints_no_sitting(stores):
    """Opening a problem records nothing: `log.md` waits for the first clock
    press or submission."""
    problems, sittings = stores

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert served.sitting is None and served.elapsed_sec is None
    assert sittings.all() == []


def test_beginning_stores_the_sitting_it_returns(stores):
    """The sitting is on disk before the clock press returns, so a restart
    between the press and the submission loses no start."""
    problems, sittings = stores

    one = begin(problems, sittings, "p1", user_id="u-4f9c2a")

    assert sittings.get(one.id) == one
    assert one.started_at > BEGAN and one.clock_started_at is None


def test_the_statement_and_title_come_through(stores):
    served = serve(*stores, "p1", user_id="u-4f9c2a")

    assert (served.title, served.statement) == ("Rotated", "Given xs ...")


def test_the_signature_is_split_from_the_prose(stores):
    """A parameter like `max_cost` read as markdown is an emphasis, so the page
    gets the line apart and shows it as code."""
    assert serve(*stores, "p1", user_id="u-4f9c2a").signature == "def solve(xs):"


def test_a_signature_in_a_fenced_block_is_split_with_its_fence(database):
    problems = ProblemStore(database)
    statement = (
        "Find the centre.\n\n```python\ndef solve(n: int, edges: list[list[int]]) -> int:\n```\n"
    )
    problems.put(make_problem("p1", statement=statement))

    served = serve(problems, SittingStore(database), "p1", user_id="u-4f9c2a")

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
def test_a_statement_not_ending_on_the_line_is_all_prose(database, statement):
    """A mention of the call inside a sentence is not the declaration."""
    problems = ProblemStore(database)
    problems.put(make_problem("p1", statement=statement))

    served = serve(problems, SittingStore(database), "p1", user_id="u-4f9c2a")

    assert (served.statement, served.signature) == (statement, None)


def test_nothing_the_problem_was_written_from_is_served():
    """A target template or a technique names the form the sitting tests, so a
    field added here that carries one fails this."""
    assert set(Served.model_fields) == {"title", "statement", "signature", "sitting", "elapsed_sec"}


def test_a_second_begin_returns_the_running_sitting(stores):
    """A second tab reaches the clock already running, rather than starting
    another on the same problem."""
    problems, sittings = stores

    first = begin(problems, sittings, "p1", user_id="u-4f9c2a")
    second = begin(problems, sittings, "p1", user_id="u-4f9c2a")

    assert second.id == first.id
    assert len(sittings.all()) == 1


def test_serving_returns_the_running_sitting(stores):
    """A reload of the problem's page finds the clock it left running."""
    problems, sittings = stores
    sittings.put(a_sitting())

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert served.sitting is not None and served.sitting.id == "s0"
    assert len(sittings.all()) == 1


def test_a_paused_sitting_is_returned_paused(stores):
    """Serving resumes nothing: a page reload would otherwise restart a clock
    the user stopped."""
    problems, sittings = stores
    sittings.put(a_sitting(pauses=[{"at": BEGAN + timedelta(minutes=5)}]))

    served = serve(problems, sittings, "p1", user_id="u-4f9c2a")

    assert served.sitting is not None and served.sitting.paused


def test_an_ended_sitting_is_not_reused(stores):
    """Its elapsed time is settled, so a new press on the problem is a new
    sitting."""
    problems, sittings = stores
    sittings.put(a_sitting(ended_at=BEGAN + timedelta(minutes=30)))

    assert serve(problems, sittings, "p1", user_id="u-4f9c2a").sitting is None
    assert begin(problems, sittings, "p1", user_id="u-4f9c2a").id != "s0"
    assert len(sittings.all()) == 2


def test_another_user_s_sitting_is_not_reused(stores):
    problems, sittings = stores
    sittings.put(a_sitting(user_id="u-b71e03"))

    one = begin(problems, sittings, "p1", user_id="u-4f9c2a")

    assert one.user_id == "u-4f9c2a" and one.id != "s0"


def test_an_unknown_problem_is_refused(database):
    with pytest.raises(Missing, match="no problem"):
        serve(ProblemStore(database), SittingStore(database), "nope", user_id="u-4f9c2a")


@pytest.mark.parametrize("opened", [serve, begin])
def test_a_retired_problem_is_refused(database, opened):
    """A defective problem was never a fair test, so no clock starts on one."""
    problems = ProblemStore(database)
    problems.put(make_problem("p1", status="retired", retired_reason="defective"))

    with pytest.raises(Refused, match="retired"):
        opened(problems, SittingStore(database), "p1", user_id="u-4f9c2a")


def test_a_sitting_is_read_back_as_it_was_served(stores):
    """The problem's page names its sitting as `?sitting=`, and a reload there
    needs the statement without starting a clock."""
    problems, sittings = stores
    at = datetime.now(UTC)
    one = begin(problems, sittings, "p1", user_id="u-4f9c2a", now=at)

    read = get(problems, sittings, one.id, user_id="u-4f9c2a", now=at)

    assert (
        read.model_dump()
        == serve(problems, sittings, "p1", user_id="u-4f9c2a", now=at).model_dump()
    )
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
