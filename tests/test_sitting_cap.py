from datetime import UTC, datetime, timedelta

import pytest
from helpers import PROVENANCE, stored_problem

from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.mint import case
from algo_coach.schema import Sitting
from algo_coach.sitting import SUBMISSIONS_PER_MINUTE, TooOften, submit

STARTED = datetime(2026, 9, 10, 8, tzinfo=UTC)
TEN = datetime(2026, 9, 10, 10, tzinfo=UTC)

DOUBLE = "def solve(n):\n    return n * 2\n"


class Stores:
    """Two sittings on one problem, each a different user's."""

    def __init__(self, root) -> None:
        self.sittings = SittingStore(root)
        self.cases = CaseLog(root)
        self.log = AttemptLog(root)
        stored_problem(root, "p1")
        for sitting_id, user_id in (("s1", "u-4f9c2a"), ("s2", "u-77b3e1")):
            self.sittings.put(
                Sitting.model_validate(
                    {
                        "id": sitting_id,
                        "user_id": user_id,
                        "problem_id": "p1",
                        "started_at": STARTED,
                        # touched where the submissions land, since the bound
                        # would otherwise end a sitting left since STARTED
                        "last_active_at": TEN,
                    }
                )
            )
        self.cases.append(case("p1", [1], 2, provenance=PROVENANCE))

    def submit(self, *, at: datetime = TEN, sitting_id: str = "s1", user_id: str = "u-4f9c2a"):
        return submit(
            self.sittings, self.cases, self.log, sitting_id, DOUBLE, user_id=user_id, now=at
        )

    def fill(self, **whose: str) -> None:
        for _ in range(SUBMISSIONS_PER_MINUTE):
            self.submit(**whose)


def test_a_submission_past_the_cap_is_refused(database):
    """Each submission runs untrusted code on the server, and the broker admits
    one run at a time, so one user's burst is every other user's wait."""
    stores = Stores(database)
    stores.fill()

    with pytest.raises(TooOften, match="cap"):
        stores.submit()


def test_a_refused_submission_mints_no_attempt(database):
    """The cap is refused before the run, so the log carries what ran and
    nothing else."""
    stores = Stores(database)
    stores.fill()

    with pytest.raises(TooOften):
        stores.submit()

    assert len(stores.log.attempts("u-4f9c2a")) == SUBMISSIONS_PER_MINUTE


def test_the_cap_is_a_rate_rather_than_a_total(database):
    """The same submission stands a minute later, since the count reads the
    minute before it."""
    stores = Stores(database)
    stores.fill()

    later = stores.submit(at=TEN + timedelta(minutes=1, seconds=1))

    assert later.attempt.solved


def test_the_cap_counts_one_user_s_own_submissions(database):
    """A reader given a user reads that user's records, so one user's burst is
    not another user's refusal."""
    stores = Stores(database)
    stores.fill()

    theirs = stores.submit(sitting_id="s2", user_id="u-77b3e1")

    assert theirs.attempt.solved
