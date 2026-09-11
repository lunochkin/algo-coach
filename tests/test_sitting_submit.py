from datetime import UTC, datetime

import pytest
from helpers import PROVENANCE, stored_problem

from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.mint import case
from algo_coach.runner import RUNNER
from algo_coach.schema import CaseOutcome, Sitting
from algo_coach.sitting import DRILL_CAP_MS, Missing, Refused, Submitted, submit
from algo_coach.verifications import VerificationLog

STARTED = datetime(2026, 9, 10, 8, tzinfo=UTC)
NINE = datetime(2026, 9, 10, 9, tzinfo=UTC)
TEN = datetime(2026, 9, 10, 10, tzinfo=UTC)
ELEVEN = datetime(2026, 9, 10, 11, tzinfo=UTC)

DOUBLE = "def solve(n):\n    return n * 2\n"
TRIPLE = "def solve(n):\n    return n * 3\n"


class Stores:
    def __init__(self, root, **sitting) -> None:
        self.sittings = SittingStore(root)
        self.cases = CaseLog(root)
        self.log = AttemptLog(root)
        stored_problem(root, "p1")
        self.sittings.put(
            Sitting.model_validate(
                {"id": "s1", "user_id": "u-4f9c2a", "problem_id": "p1", "started_at": STARTED}
                | sitting
            )
        )
        stored_problem(root, "p1")
        for args, expected in (([1], 2), ([3], 6)):
            self.cases.append(case("p1", args, expected, provenance=PROVENANCE))

    def submit(
        self,
        code: str,
        *,
        now: datetime = ELEVEN,
        sitting_id: str = "s1",
        user_id: str = "u-4f9c2a",
    ):
        return self.submitted(code, now=now, sitting_id=sitting_id, user_id=user_id).attempt

    def submitted(
        self,
        code: str,
        *,
        now: datetime = ELEVEN,
        sitting_id: str = "s1",
        user_id: str = "u-4f9c2a",
    ) -> Submitted:
        return submit(
            self.sittings, self.cases, self.log, sitting_id, code, user_id=user_id, now=now
        )


def test_a_passing_submission_mints_a_solved_attempt_in_the_log(database):
    stores = Stores(database)

    attempt = stores.submit(DOUBLE)

    assert attempt.solved
    assert stores.log.attempts() == [attempt]


def test_the_attempt_names_its_sitting_and_carries_the_code(database):
    """The log is append-only, so the grouping and the code go in with the
    attempt or never."""
    attempt = Stores(database).submit(DOUBLE)

    assert (attempt.sitting_id, attempt.user_id, attempt.problem_id) == ("s1", "u-4f9c2a", "p1")
    assert (attempt.code, attempt.language) == (DOUBLE, "python")


def test_a_wrong_answer_is_unsolved(database):
    assert not Stores(database).submit(TRIPLE).solved


def test_a_failing_submission_shows_the_first_case_it_failed_whole(database):
    """`flows.md`: an outcome on an input the solver cannot see is debugged by
    guessing."""
    second_wrong = "def solve(n):\n    return 2 if n == 1 else 0\n"

    failure = Stores(database).submitted(second_wrong).failure

    assert (failure.outcome, failure.args, failure.expected, failure.returned) == (
        CaseOutcome.WRONG,
        [3],
        6,
        0,
    )
    assert failure.error is None


def test_the_first_failure_is_first_in_the_problem_s_case_order(database):
    """The statement's own cases are written first, so the small example is
    the one shown rather than the separating input."""
    stores = Stores(database)

    assert stores.submitted(TRIPLE).failure.args == [1]


def test_a_passing_submission_shows_no_failure(database):
    assert Stores(database).submitted(DOUBLE).failure is None


def test_a_crash_shows_the_case_and_no_returned_value(database):
    """A value shown beside a crash would be one the submission never
    returned."""
    raising = "def solve(n):\n    raise ValueError(n)\n"

    failure = Stores(database).submitted(raising).failure

    assert (failure.outcome, failure.args, failure.expected) == (CaseOutcome.CRASHED, [1], 2)
    assert failure.returned is None
    assert failure.error.rstrip().endswith("ValueError: 1")


def test_code_defining_no_solve_is_unsolved(database):
    """A submission with a syntax error is the ordinary case, and a verdict
    rather than an error."""
    assert not Stores(database).submit("def solve(n)\n").solved


def test_only_the_sitting_s_problem_decides(database):
    """A case of another problem would fail every correct submission here."""
    stores = Stores(database)
    stored_problem(database, "p2")
    stores.cases.append(case("p2", [1], 99, provenance=PROVENANCE))

    assert stores.submit(DOUBLE).solved


def test_the_run_is_capped_at_the_sitting_s_cap(database, monkeypatch):
    """Generation's cap sits well above the sitting's, and a submission is
    judged under the one the separating case was chosen against."""
    monkeypatch.setattr("algo_coach.sitting.DRILL_CAP_MS", 50)
    slow = "import time\n\n\ndef solve(n):\n    time.sleep(0.5)\n    return n * 2\n"

    assert not Stores(database).submit(slow).solved


def test_the_elapsed_time_runs_from_the_start_to_the_submission(database):
    """The attempt carries the sitting's clock at the moment of submission,
    with every pause excluded."""
    stores = Stores(database, pauses=[{"at": NINE, "until": TEN}])

    attempt = stores.submit(DOUBLE, now=ELEVEN)

    assert attempt.started_at == STARTED and attempt.finished_at == ELEVEN
    assert attempt.time_to_solve_sec == 2 * 3600.0


def test_a_second_submission_is_a_second_attempt_on_a_cumulative_clock(database):
    """A sitting mints an attempt per submission, and each carries the whole
    time since the statement was served."""
    stores = Stores(database)

    first = stores.submit(TRIPLE, now=NINE)
    second = stores.submit(DOUBLE, now=TEN)

    assert (first.time_to_solve_sec, second.time_to_solve_sec) == (3600.0, 7200.0)
    assert {one.sitting_id for one in stores.log.attempts()} == {"s1"}


def test_submitting_leaves_the_sitting_running(database):
    """Ending is the loop's call: a failed submission is followed by another."""
    stores = Stores(database)
    stores.submit(TRIPLE)

    assert stores.sittings.get("s1").ended_at is None


def test_a_paused_sitting_takes_no_submission(database):
    """The clock is stopped, so the attempt would carry time the engine did not
    count for it."""
    stores = Stores(database, pauses=[{"at": NINE}])

    with pytest.raises(Refused, match="paused"):
        stores.submit(DOUBLE)
    assert stores.log.attempts() == []


def test_an_ended_sitting_takes_no_submission(database):
    stores = Stores(database, ended_at=TEN)

    with pytest.raises(Refused, match="has ended"):
        stores.submit(DOUBLE)


def test_an_unknown_sitting_is_refused(database):
    with pytest.raises(Missing, match="no sitting"):
        Stores(database).submit(DOUBLE, sitting_id="nope")


def test_another_user_s_sitting_takes_no_submission(database):
    """The attempt would land in the owner's log under a submission they never
    made."""
    stores = Stores(database)

    with pytest.raises(Missing, match="no sitting"):
        stores.submit(DOUBLE, user_id="u-b71e03")
    assert stores.log.attempts() == []


def test_the_verification_is_stored_beside_the_attempt(database):
    """The log is append-only, so the per-case verdict goes in with the attempt
    or is never readable."""
    stores = Stores(database)

    submitted = stores.submitted(TRIPLE)

    assert stores.log.verifications() == [submitted.verification]
    assert submitted.verification.attempt_id == submitted.attempt.id


def test_the_verification_names_the_cap_and_the_runner(database):
    """A timeout means nothing without the cap it hit, and two runs are
    comparable only within one runner."""
    verification = Stores(database).submitted(DOUBLE).verification

    assert (verification.cap_ms, verification.runner) == (DRILL_CAP_MS, RUNNER)


def test_every_case_carries_its_own_outcome(database):
    """A wrong answer on one case and a pass on another is what a solver needs
    to read, and `solved` alone drops it."""
    stores = Stores(database)
    stores.cases.append(case("p1", [5], 11, provenance=PROVENANCE))

    verification = stores.submitted(DOUBLE).verification

    assert [one.outcome for one in verification.results] == [
        CaseOutcome.PASSED,
        CaseOutcome.PASSED,
        CaseOutcome.WRONG,
    ]


def test_solved_is_the_projection_of_the_verification(database):
    """One rule decides both, so the attempt and its verdict cannot disagree."""
    stores = Stores(database)

    for code in (DOUBLE, TRIPLE, "def solve(n)\n"):
        submitted = stores.submitted(code)
        assert submitted.attempt.solved is submitted.verification.verified


def test_a_crash_is_a_verdict_on_every_case(database):
    verification = Stores(database).submitted("def solve(n)\n").verification

    assert {one.outcome for one in verification.results} == {CaseOutcome.CRASHED}


def test_the_user_s_results_never_reach_the_product_store(database):
    """The global verification log ships with the corpus, and the user's own
    code is private."""
    Stores(database).submitted(DOUBLE)

    assert VerificationLog(database).verifications() == []


def test_a_refused_submission_stores_no_verification(database):
    stores = Stores(database, pauses=[{"at": NINE}])

    with pytest.raises(Refused, match="paused"):
        stores.submitted(DOUBLE)
    assert stores.log.verifications() == []
