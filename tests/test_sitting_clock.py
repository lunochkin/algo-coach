from datetime import UTC, datetime, timedelta

import pytest

from algo_coach.log import SittingStore
from algo_coach.schema import Sitting
from algo_coach.sitting import end, pause, resume

STARTED = datetime(2026, 9, 10, 8, tzinfo=UTC)
NINE = datetime(2026, 9, 10, 9, tzinfo=UTC)
TEN = datetime(2026, 9, 10, 10, tzinfo=UTC)
ELEVEN = datetime(2026, 9, 10, 11, tzinfo=UTC)


def a_store(tmp_path, **overrides) -> SittingStore:
    store = SittingStore(tmp_path)
    store.put(
        Sitting.model_validate(
            {"id": "s1", "user_id": "maks", "problem_id": "p1", "started_at": STARTED} | overrides
        )
    )
    return store


def test_a_pause_stops_the_clock(tmp_path):
    """The interval opens where the user stepped away, and nothing after it
    counts until a resume."""
    store = a_store(tmp_path)

    one = pause(store, "s1", now=NINE)

    assert one.paused and one.pauses[-1].at == NINE
    assert one.elapsed(ELEVEN) == 3600.0


def test_a_resume_closes_the_interval(tmp_path):
    """The hours away leave the elapsed time, and the sitting runs again."""
    store = a_store(tmp_path)
    pause(store, "s1", now=NINE)

    one = resume(store, "s1", now=TEN)

    assert not one.paused
    assert one.elapsed(ELEVEN) == 2 * 3600.0


def test_the_store_holds_what_the_call_returned(tmp_path):
    """The call writes the record it returns, so a caller that only stored the
    sitting id reads the same clock back."""
    store = a_store(tmp_path)

    assert pause(store, "s1", now=NINE) == store.get("s1")


def test_ending_closes_a_pause_nobody_resumed(tmp_path):
    """A sitting ends with no pause open, and the pause the user never came
    back from covers the time away."""
    store = a_store(tmp_path)
    pause(store, "s1", now=NINE)

    one = end(store, "s1", now=ELEVEN)

    assert one.ended_at == ELEVEN and not one.paused
    assert one.elapsed(ELEVEN) == 3600.0


def test_ending_a_running_sitting_leaves_its_pauses(tmp_path):
    store = a_store(tmp_path)

    one = end(store, "s1", now=TEN)

    assert one.pauses == [] and one.elapsed(ELEVEN) == 2 * 3600.0


def test_pausing_twice_is_refused(tmp_path):
    """A second open interval would make the elapsed time depend on which one
    a reader took."""
    store = a_store(tmp_path)
    pause(store, "s1", now=NINE)

    with pytest.raises(ValueError, match="already paused"):
        pause(store, "s1", now=TEN)


def test_resuming_a_running_sitting_is_refused(tmp_path):
    """Nothing is stopped, so a resume would close an interval that does not
    exist."""
    with pytest.raises(ValueError, match="not paused"):
        resume(a_store(tmp_path), "s1", now=NINE)


@pytest.mark.parametrize("call", [pause, resume, end])
def test_an_ended_sitting_takes_no_more_calls(tmp_path, call):
    """Its elapsed time is settled, and a later interval would move it."""
    store = a_store(tmp_path, ended_at=TEN)

    with pytest.raises(ValueError, match="has ended"):
        call(store, "s1", now=ELEVEN)


@pytest.mark.parametrize("call", [pause, resume, end])
def test_an_unknown_sitting_is_refused(tmp_path, call):
    with pytest.raises(ValueError, match="no sitting"):
        call(SittingStore(tmp_path), "nope", now=NINE)


def test_the_engine_s_clock_is_the_default(tmp_path):
    """The loop passes no time of its own, so a duration the browser reports
    reaches no record."""
    began = datetime.now(UTC) - timedelta(minutes=1)
    store = a_store(tmp_path, started_at=began)

    one = pause(store, "s1")

    assert one.pauses[-1].at > began
