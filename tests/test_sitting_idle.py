from datetime import UTC, datetime, timedelta

import pytest
from helpers import PROVENANCE, stored_problem

from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.mint import case
from algo_coach.problems import ProblemStore
from algo_coach.schema import Sitting
from algo_coach.sitting import IDLE_MINUTES, Refused, end, get, pause, resume, serve, submit

STARTED = datetime(2026, 9, 10, 10, tzinfo=UTC)
SOON = STARTED + timedelta(minutes=5)
LATER = STARTED + timedelta(minutes=IDLE_MINUTES + 1)

USER = "u-4f9c2a"
DOUBLE = "def solve(n):\n    return n * 2\n"


class Stores:
    def __init__(self, root, **sitting: object) -> None:
        self.problems = ProblemStore(root)
        self.sittings = SittingStore(root)
        self.cases = CaseLog(root)
        self.log = AttemptLog(root)
        stored_problem(root, "p1")
        self.cases.append(case("p1", [1], 2, provenance=PROVENANCE))
        self.sittings.put(
            Sitting.model_validate(
                {
                    "id": "s1",
                    "user_id": USER,
                    "problem_id": "p1",
                    "started_at": STARTED,
                    "last_active_at": STARTED,
                }
                | sitting
            )
        )

    def served(self, at: datetime):
        return serve(self.problems, self.sittings, "p1", user_id=USER, now=at)

    def read(self, at: datetime):
        return get(self.problems, self.sittings, "s1", user_id=USER, now=at)

    def submitted(self, at: datetime):
        return submit(self.sittings, self.cases, self.log, "s1", DOUBLE, user_id=USER, now=at)


def test_serving_again_within_the_bound_reaches_the_running_clock(database):
    """A refresh or a second tab reaches the clock already running."""
    stores = Stores(database)

    served = stores.served(SOON)

    assert served.sitting.id == "s1"
    assert served.sitting.last_active_at == SOON
    assert served.elapsed_sec == 300


def test_serving_after_the_bound_ends_the_idle_sitting_where_it_was_left(database):
    """The clock stopped where the user left, so the ended sitting reports the
    time it ran rather than the hours since."""
    stores = Stores(database)

    served = stores.served(LATER)

    left = stores.sittings.get("s1")
    assert left is not None
    assert left.ended_at == STARTED
    assert served.sitting.id != "s1"
    assert served.elapsed_sec == 0


def test_reading_an_idle_sitting_ends_it_at_its_last_activity(database):
    """The ending is read-time, so the elapsed time does not move with the
    moment a reader arrives."""
    stores = Stores(database)

    read = stores.read(LATER)

    assert read.sitting.ended_at == STARTED
    assert read.elapsed_sec == 0


def test_an_idle_sitting_closes_the_pause_the_user_left_open(database):
    """An ended sitting holds no open pause."""
    stores = Stores(database)
    pause(stores.sittings, "s1", user_id=USER, now=SOON)

    # the pause touched the sitting, so the bound counts from it
    read = stores.read(SOON + timedelta(minutes=IDLE_MINUTES + 1))

    assert read.sitting.ended_at == SOON
    assert read.sitting.pauses[-1].until == SOON


def test_a_submission_to_an_idle_sitting_is_refused_and_ends_it(database):
    """The elapsed time that attempt would carry counts the hours away."""
    stores = Stores(database)

    with pytest.raises(Refused, match="idle"):
        stores.submitted(LATER)

    left = stores.sittings.get("s1")
    assert left is not None and left.ended_at == STARTED
    assert stores.log.attempts(USER) == []


def test_a_submission_within_the_bound_touches_the_sitting(database):
    """A submission is the loop acting, so the bound counts from it."""
    stores = Stores(database)

    stores.submitted(SOON)

    left = stores.sittings.get("s1")
    assert left is not None and left.last_active_at == SOON


def test_a_pause_and_a_resume_each_touch_the_sitting(database):
    """A solver stepping away on purpose has not abandoned the sitting."""
    stores = Stores(database)

    paused = pause(stores.sittings, "s1", user_id=USER, now=SOON)
    resumed = resume(stores.sittings, "s1", user_id=USER, now=SOON + timedelta(minutes=1))

    assert paused.last_active_at == SOON
    assert resumed.last_active_at == SOON + timedelta(minutes=1)


def test_ending_a_sitting_leaves_its_last_activity_alone(database):
    """The two timestamps say which ended a sitting: equal where the bound did,
    and an `ended_at` later where the user pressed End."""
    stores = Stores(database)

    ended = end(stores.sittings, "s1", user_id=USER, now=SOON)

    assert (ended.last_active_at, ended.ended_at) == (STARTED, SOON)
