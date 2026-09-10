from datetime import timedelta

import pytest
from helpers import PROVENANCE, make_problem

from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.mint import case
from algo_coach.problems import ProblemStore
from algo_coach.sitting import end, pause, resume, serve, submit

USER = "u-4f9c2a"
DOUBLE = "def solve(n):\n    return n * 2\n"
TRIPLE = "def solve(n):\n    return n * 3\n"


@pytest.fixture
def root(tmp_path):
    ProblemStore(tmp_path).put(make_problem("p1", statement="Double n.\n\ndef solve(n):"))
    for args, expected in (([1], 2), ([3], 6)):
        CaseLog(tmp_path).append(case("p1", args, expected, provenance=PROVENANCE))
    return tmp_path


def test_one_sitting_runs_from_serve_to_end(root):
    """Every store reads from one root, as the adapter will open them, so a
    call that wrote where the next one does not read fails here and nowhere
    else."""
    problems, sittings, cases, log = (
        ProblemStore(root),
        SittingStore(root),
        CaseLog(root),
        AttemptLog(root),
    )

    served = serve(problems, sittings, "p1", user_id=USER)
    sitting_id, began = served.sitting.id, served.sitting.started_at

    pause(sittings, sitting_id, user_id=USER, now=began + timedelta(minutes=5))
    resume(sittings, sitting_id, user_id=USER, now=began + timedelta(minutes=15))
    failing = submit(
        sittings, cases, log, sitting_id, TRIPLE, user_id=USER, now=began + timedelta(minutes=20)
    ).attempt
    passing = submit(
        sittings, cases, log, sitting_id, DOUBLE, user_id=USER, now=began + timedelta(minutes=30)
    ).attempt
    ended = end(sittings, sitting_id, user_id=USER, now=began + timedelta(minutes=31))

    assert log.attempts() == [failing, passing]
    assert [one.solved for one in log.attempts()] == [False, True]
    assert {one.sitting_id for one in log.attempts()} == {sitting_id}
    assert [one.attempt_id for one in log.verifications()] == [failing.id, passing.id]
    # cumulative from the start, the ten paused minutes left out of both
    assert (failing.time_to_solve_sec, passing.time_to_solve_sec) == (600.0, 1200.0)
    assert sittings.all() == [ended]
    assert ended.ended_at is not None and not ended.paused


def test_a_serve_after_the_end_starts_a_new_sitting(root):
    """The ended sitting's clock is settled, so the next visit to the problem
    is timed on its own."""
    problems, sittings = ProblemStore(root), SittingStore(root)
    first = serve(problems, sittings, "p1", user_id=USER).sitting
    end(sittings, first.id, user_id=USER, now=first.started_at + timedelta(minutes=1))

    second = serve(problems, sittings, "p1", user_id=USER).sitting

    assert second.id != first.id
    with pytest.raises(ValueError, match="has ended"):
        submit(sittings, CaseLog(root), AttemptLog(root), first.id, DOUBLE, user_id=USER)
