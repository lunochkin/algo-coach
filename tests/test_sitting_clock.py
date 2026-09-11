from datetime import UTC, datetime, timedelta

import pytest
from helpers import stored_problem

from algo_coach.log import SittingStore
from algo_coach.schema import Sitting
from algo_coach.sitting import Missing, Refused, end, pause, resume


@pytest.fixture(autouse=True)
def referenced(database):
    """The problem this module's sittings and attempts name."""
    stored_problem(database, "p1")


STARTED = datetime(2026, 9, 10, 8, tzinfo=UTC)
NINE = datetime(2026, 9, 10, 9, tzinfo=UTC)
TEN = datetime(2026, 9, 10, 10, tzinfo=UTC)
ELEVEN = datetime(2026, 9, 10, 11, tzinfo=UTC)


def a_store(database, **overrides) -> SittingStore:
    store = SittingStore(database)
    store.put(
        Sitting.model_validate(
            {"id": "s1", "user_id": "u-4f9c2a", "problem_id": "p1", "started_at": STARTED}
            | overrides
        )
    )
    return store


def test_a_pause_stops_the_clock(database):
    """The interval opens where the user stepped away, and nothing after it
    counts until a resume."""
    store = a_store(database)

    one = pause(store, "s1", user_id="u-4f9c2a", now=NINE)

    assert one.paused and one.pauses[-1].at == NINE
    assert one.elapsed(ELEVEN) == 3600.0


def test_a_resume_closes_the_interval(database):
    """The hours away leave the elapsed time, and the sitting runs again."""
    store = a_store(database)
    pause(store, "s1", user_id="u-4f9c2a", now=NINE)

    one = resume(store, "s1", user_id="u-4f9c2a", now=TEN)

    assert not one.paused
    assert one.elapsed(ELEVEN) == 2 * 3600.0


def test_the_store_holds_what_the_call_returned(database):
    """The call writes the record it returns, so a caller that only stored the
    sitting id reads the same clock back."""
    store = a_store(database)

    assert pause(store, "s1", user_id="u-4f9c2a", now=NINE) == store.get("s1")


def test_ending_closes_a_pause_nobody_resumed(database):
    """A sitting ends with no pause open, and the pause the user never came
    back from covers the time away."""
    store = a_store(database)
    pause(store, "s1", user_id="u-4f9c2a", now=NINE)

    one = end(store, "s1", user_id="u-4f9c2a", now=ELEVEN)

    assert one.ended_at == ELEVEN and not one.paused
    assert one.elapsed(ELEVEN) == 3600.0


def test_ending_a_running_sitting_leaves_its_pauses(database):
    store = a_store(database)

    one = end(store, "s1", user_id="u-4f9c2a", now=TEN)

    assert one.pauses == [] and one.elapsed(ELEVEN) == 2 * 3600.0


def test_pausing_twice_is_refused(database):
    """A second open interval would make the elapsed time depend on which one
    a reader took."""
    store = a_store(database)
    pause(store, "s1", user_id="u-4f9c2a", now=NINE)

    with pytest.raises(Refused, match="already paused"):
        pause(store, "s1", user_id="u-4f9c2a", now=TEN)


def test_resuming_a_running_sitting_is_refused(database):
    """Nothing is stopped, so a resume would close an interval that does not
    exist."""
    with pytest.raises(Refused, match="not paused"):
        resume(a_store(database), "s1", user_id="u-4f9c2a", now=NINE)


@pytest.mark.parametrize("call", [pause, resume, end])
def test_an_ended_sitting_takes_no_more_calls(database, call):
    """Its elapsed time is settled, and a later interval would move it."""
    store = a_store(database, ended_at=TEN)

    with pytest.raises(Refused, match="has ended"):
        call(store, "s1", user_id="u-4f9c2a", now=ELEVEN)


@pytest.mark.parametrize("call", [pause, resume, end])
def test_an_unknown_sitting_is_refused(database, call):
    with pytest.raises(Missing, match="no sitting"):
        call(SittingStore(database), "nope", user_id="u-4f9c2a", now=NINE)


def test_the_engine_s_clock_is_the_default(database):
    """The loop passes no time of its own, so a duration the browser reports
    reaches no record."""
    began = datetime.now(UTC) - timedelta(minutes=1)
    store = a_store(database, started_at=began)

    one = pause(store, "s1", user_id="u-4f9c2a")

    assert one.pauses[-1].at > began


@pytest.mark.parametrize("call", [pause, resume, end])
def test_another_user_s_sitting_reads_as_missing(database, call):
    """Holding a sitting id grants nothing, and the refusal does not say the
    sitting exists."""
    with pytest.raises(Missing, match="no sitting"):
        call(a_store(database), "s1", user_id="u-b71e03", now=NINE)
