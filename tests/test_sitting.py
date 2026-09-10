from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from algo_coach.mint import sitting
from algo_coach.schema import Sitting

CONTENT = {
    "id": "s1",
    "user_id": "u-4f9c2a",
    "problem_id": "p1",
    "started_at": "2026-09-10T08:00:00Z",
}
AT_NINE = "2026-09-10T09:00:00Z"
AT_TEN = "2026-09-10T10:00:00Z"
NOW = datetime(2026, 9, 10, 12, tzinfo=UTC)


@pytest.mark.parametrize("field", ["id", "user_id", "problem_id", "started_at"])
def test_a_sitting_needs_every_field(field):
    """A sitting with no start times nothing, and one with no problem says
    nothing about what was served."""
    with pytest.raises(ValidationError):
        Sitting.model_validate({k: v for k, v in CONTENT.items() if k != field})


@pytest.mark.parametrize("field", ["user_id", "problem_id"])
def test_an_empty_reference_is_rejected(field):
    """An empty string passes a presence check while naming nothing."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT | {field: ""})


def test_a_sitting_is_frozen():
    """The store replaces the record; nothing edits one in place."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT).id = "s2"


def test_the_minted_start_is_the_engine_s_own():
    """The clock a duration is measured from is the engine's, never a number a
    caller passed in."""
    one = sitting("u-4f9c2a", "p1")
    assert one.id and one.started_at.tzinfo is not None
    assert (one.user_id, one.problem_id) == ("u-4f9c2a", "p1")


def test_two_sittings_carry_different_ids():
    """The id groups a sitting's attempts, so two sittings may not share one."""
    assert sitting("u-4f9c2a", "p1").id != sitting("u-4f9c2a", "p1").id


def a_pause(at, until=None) -> dict:
    return {"at": at, "until": until}


def test_a_pause_ends_no_earlier_than_it_starts():
    """An interval running backwards would subtract time from the sitting."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT | {"pauses": [a_pause(AT_TEN, AT_NINE)]})


def test_a_pause_starts_after_the_sitting():
    """A pause before the statement was served covers time nobody sat."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT | {"pauses": [a_pause("2026-09-10T07:00:00Z")]})


def test_pauses_do_not_overlap():
    """Overlapping intervals count the same minutes twice."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(
            CONTENT | {"pauses": [a_pause(AT_NINE, AT_TEN), a_pause(AT_NINE, AT_TEN)]}
        )


def test_only_the_last_pause_is_open():
    """An open pause with another after it is a state no sequence of calls
    produces."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT | {"pauses": [a_pause(AT_NINE), a_pause(AT_TEN)]})


def test_a_sitting_ends_with_no_pause_open():
    """The elapsed time would otherwise move with the moment it is read."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(CONTENT | {"pauses": [a_pause(AT_NINE)], "ended_at": AT_TEN})


def test_a_sitting_ends_after_its_last_pause():
    """A sitting that ended before it resumed leaves the pause outside it."""
    with pytest.raises(ValidationError):
        Sitting.model_validate(
            CONTENT | {"pauses": [a_pause(AT_NINE, AT_TEN)], "ended_at": AT_NINE}
        )


def test_the_elapsed_time_excludes_every_pause():
    """The clock stops for a pause, so the hours away are not time spent
    solving."""
    one = Sitting.model_validate(
        CONTENT | {"pauses": [a_pause(AT_NINE, AT_TEN)], "ended_at": "2026-09-10T11:00:00Z"}
    )
    assert one.elapsed(NOW) == 2 * 3600.0


def test_an_open_pause_stops_the_clock_at_the_moment_it_is_read():
    """A running sitting has no end, so both ends of the count come from
    `now`."""
    one = Sitting.model_validate(CONTENT | {"pauses": [a_pause(AT_NINE)]})
    assert one.paused
    assert one.elapsed(NOW) == 3600.0


def test_a_running_sitting_counts_to_now():
    """A sitting with no pause and no end elapsed everything since it began."""
    assert Sitting.model_validate(CONTENT).elapsed(NOW) == 4 * 3600.0
