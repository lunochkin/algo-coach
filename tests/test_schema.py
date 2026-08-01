from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from algo_coach.log import AttemptLog
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    Diagnosis,
    FailureMode,
    Technique,
    TechniqueClaim,
    TestResult,
)


def make_attempt(id: str, self_label: FailureMode | None) -> Attempt:
    now = datetime.now(UTC)
    return Attempt(
        id=id,
        started_at=now,
        finished_at=now,
        problem_id="p1",
        user_id="user1",
        code="def f(): pass",
        tests=[TestResult(name="t1", passed=False)],
        solved=False,
        origin=AttemptOrigin.ENGINE,
        time_to_solve_sec=900.0,
        self_label=self_label,
    )


def test_a_backfilled_attempt_needs_only_when_it_landed():
    """A platform records the submission time and little else. Requiring a
    start, a duration or the code would reject the whole backlog."""
    attempt = Attempt(
        id="a1",
        user_id="u1",
        problem_id="p1",
        finished_at=datetime.now(UTC),
        solved=True,
        origin=AttemptOrigin.PUSH,
    )
    assert attempt.started_at is None
    assert attempt.time_to_solve_sec is None
    assert attempt.code is None


def test_a_pushed_attempt_cannot_claim_engine_origin():
    """An external_id only exists on the push path, so a record carrying one
    and claiming the engine produced it is rejected outright."""
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        Attempt(
            id="a1",
            external_id="e1",
            user_id="u1",
            problem_id="p1",
            started_at=now,
            finished_at=now,
            code="def f(): pass",
            solved=True,
            origin=AttemptOrigin.ENGINE,
            time_to_solve_sec=900.0,
        )


def make_diagnosis(attempt_id: str, mode: FailureMode) -> Diagnosis:
    return Diagnosis(
        attempt_id=attempt_id,
        mode=mode,
        confidence=0.8,
        evidence="loop bound off by one",
        model="test-model",
        prompt_version="v0",
        created_at=datetime.now(UTC),
    )


def test_attempt_roundtrip(tmp_path):
    log = AttemptLog(tmp_path)
    attempt = make_attempt("a1", FailureMode.RUST)
    log.append_attempt(attempt)
    log.append_diagnosis(make_diagnosis("a1", FailureMode.RUST))

    assert log.attempts() == [attempt]
    assert log.diagnoses()[0].attempt_id == "a1"


def test_technique_claim_records_its_source():
    claim = TechniqueClaim(
        id="c1",
        created_at=datetime.now(UTC),
        attempt_id="a1",
        techniques=["backtracking"],
        source=ClaimSource.USER,
    )

    assert claim.source is ClaimSource.USER


def test_a_claim_names_every_technique_at_once():
    """One record per attempt, so a revision replaces the whole set."""
    claim = make_claim(ClaimSource.USER, techniques=["backtracking", "recursion"])

    assert claim.techniques == ["backtracking", "recursion"]


def test_a_claim_names_at_least_one_technique():
    with pytest.raises(ValidationError):
        make_claim(ClaimSource.USER, techniques=[])


def test_technique_claim_requires_a_source():
    """Nothing distinguishes a user claim from a machine one after the fact."""
    with pytest.raises(ValidationError):
        TechniqueClaim(
            id="c1",
            created_at=datetime.now(UTC),
            attempt_id="a1",
            techniques=["backtracking"],
        )


def make_claim(source: ClaimSource, **overrides) -> TechniqueClaim:
    fields = {
        "id": "c1",
        "created_at": datetime.now(UTC),
        "attempt_id": "a1",
        "techniques": ["backtracking"],
        "source": source,
    } | overrides
    return TechniqueClaim.model_validate(fields)


def test_classifier_claim_records_what_produced_it():
    claim = make_claim(ClaimSource.CLASSIFIER, model="test-model", prompt_version="v0")

    assert (claim.model, claim.prompt_version) == ("test-model", "v0")


def test_classifier_claim_without_a_version_is_rejected():
    """Re-deriving machine claims means knowing which ones are stale."""
    with pytest.raises(ValidationError):
        make_claim(ClaimSource.CLASSIFIER)


def test_user_claim_carries_no_version():
    with pytest.raises(ValidationError):
        make_claim(ClaimSource.USER, model="test-model", prompt_version="v0")


@pytest.mark.parametrize("code", ["", "  ", "../evil", "a/b", "Foo", "-leading-dash"])
def test_technique_code_must_be_a_safe_slug(code):
    with pytest.raises(ValidationError):
        Technique(code=code)


@pytest.mark.parametrize("code", ["monotonic-stack", "backtracking"])
def test_technique_code_accepts_slug(code):
    assert Technique(code=code).code == code
