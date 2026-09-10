from datetime import UTC, datetime

import pytest

from algo_coach.attempt_claims import standing_attempt_claims
from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt, ClaimSource, Confidence
from algo_coach.sitting import claim

USER = "u-4f9c2a"
CANDIDATES = ["binary-search", "sorting"]


@pytest.fixture
def log(tmp_path) -> AttemptLog:
    one = AttemptLog(tmp_path)
    one.append_attempt(
        Attempt(
            id="a1",
            user_id=USER,
            problem_id="p1",
            sitting_id="s1",
            finished_at=datetime(2026, 9, 10, 9, tzinfo=UTC),
            solved=True,
        )
    )
    return one


def claimed(log, techniques, **overrides):
    fields = {"candidates": CANDIDATES, "user_id": USER, "confidence": Confidence.SURE}
    return claim(log, "a1", techniques, **(fields | overrides))


def test_the_answer_is_stored_as_the_user_s_claim(log):
    """The loop asks while the attempt is minutes old, and the answer stands
    over any machine claim written later."""
    written = claimed(log, ["binary-search"])

    assert log.claims() == [written]
    assert (written.source, written.techniques, written.confidence) == (
        ClaimSource.USER,
        ["binary-search"],
        Confidence.SURE,
    )
    assert standing_attempt_claims(log.claims())["a1"] == written


def test_nothing_was_in_view_but_the_code(log):
    """A claim made with a machine claim shown measures that configuration
    against itself, and the sitting shows none."""
    assert claimed(log, ["sorting"]).informed_by == []


def test_a_stated_decline_is_stored(log):
    """None of the problem's techniques is a verdict about the code, and
    distinct from a skipped question."""
    written = claimed(log, [], declined=True)

    assert written.declined and written.techniques == []


def test_naming_nothing_without_declining_is_refused(log):
    """An empty set would make a lost answer and a stated verdict one record."""
    with pytest.raises(ValueError, match="at least one technique"):
        claimed(log, [])
    assert log.claims() == []


def test_a_technique_outside_the_problem_s_own_is_refused(log):
    """The candidates are the problem's techniques, and the scores compare over
    that set."""
    with pytest.raises(ValueError, match="greedy"):
        claimed(log, ["binary-search", "greedy"])
    assert log.claims() == []


def test_a_later_answer_stands_over_an_earlier_one(log):
    """A claim can be revised, since the code it reads does not decay."""
    claimed(log, ["binary-search"])
    later = claimed(log, ["binary-search", "sorting"], confidence=Confidence.LEANING)

    assert standing_attempt_claims(log.claims())["a1"] == later


def test_another_user_s_attempt_reads_as_missing(log):
    with pytest.raises(ValueError, match="no attempt"):
        claimed(log, ["sorting"], user_id="u-b71e03")
    assert log.claims() == []


def test_an_unknown_attempt_is_refused(log):
    with pytest.raises(ValueError, match="no attempt"):
        claim(
            log,
            "nope",
            ["sorting"],
            candidates=CANDIDATES,
            user_id=USER,
            confidence=Confidence.SURE,
        )
