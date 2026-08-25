from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from algo_coach.log import AttemptLog
from algo_coach.schema import (
    Attempt,
    AttemptRecord,
    ClaimSource,
    Confidence,
    Diagnosis,
    FailureMode,
    Kind,
    SelfLabel,
    Technique,
    TechniqueClaim,
)


def entry(code: str) -> Technique:
    """A vocabulary entry with the criterion fields filled in, so a test about
    the code says only that."""
    return Technique(code=code, kind=Kind.PROCEDURE, earns="e", near_miss="n")


def make_attempt(id: str) -> Attempt:
    now = datetime.now(UTC)
    return Attempt(
        id=id,
        started_at=now,
        finished_at=now,
        problem_id="p1",
        user_id="user1",
        code="def f(): pass",
        solved=False,
        time_to_solve_sec=900.0,
    )


def make_diagnosis(attempt_id: str, mode: FailureMode) -> Diagnosis:
    return Diagnosis(
        id=f"d-{attempt_id}",
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
    attempt = make_attempt("a1")
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


PROVENANCE = {
    "model": "test-model",
    "effort": "medium",
    "pin": "a-host",
    "prompt_hash": "0123456789ab",
    "call_id": "call-1",
}


def test_classifier_claim_records_what_produced_it():
    claim = make_claim(ClaimSource.CLASSIFIER, **PROVENANCE)

    assert {field: getattr(claim, field) for field in PROVENANCE} == PROVENANCE


def test_classifier_claim_without_any_provenance_is_rejected():
    """Re-deriving machine claims means knowing which ones are stale."""
    with pytest.raises(ValidationError):
        make_claim(ClaimSource.CLASSIFIER)


@pytest.mark.parametrize("missing", PROVENANCE)
def test_classifier_claim_needs_every_field_that_produced_it(missing):
    """All of them or none. A reading whose configuration is partly unknown
    cannot be compared with one whose configuration is known, and a reader
    would branch on the absence forever."""
    with pytest.raises(ValidationError, match=missing):
        make_claim(
            ClaimSource.CLASSIFIER,
            **{field: value for field, value in PROVENANCE.items() if field != missing},
        )


@pytest.mark.parametrize("field", PROVENANCE)
def test_user_claim_carries_no_provenance(field):
    """Nothing re-derives a user's claim, so naming a model would name one
    that never touched it."""
    with pytest.raises(ValidationError, match=field):
        make_claim(ClaimSource.USER, **{field: PROVENANCE[field]})


def test_a_claim_is_blind_unless_it_says_otherwise():
    """The absence of a reading is the ordinary case — the drill loop asks
    before any classifier has run — so an empty list is what a claim means
    when nothing recorded what its author saw."""
    assert make_claim(ClaimSource.USER).informed_by == []


def test_a_user_claim_records_the_readings_its_author_saw():
    """Not provenance: provenance is what produced a claim, this is what its
    author had in view. A user claim carries the second and never the first."""
    claim = make_claim(ClaimSource.USER, informed_by=["call-1", "call-2"])

    assert claim.informed_by == ["call-1", "call-2"]


def test_readings_are_named_one_by_one_rather_than_flagged():
    """A claim made after seeing one configuration's reading is still
    independent of another's, and configurations are scored against the same
    claims — so validity is per configuration, which a boolean cannot say."""
    claim = make_claim(ClaimSource.USER, informed_by=["call-1"])

    assert "call-1" in claim.informed_by
    assert "call-2" not in claim.informed_by


def test_a_claim_carries_no_confidence_unless_asked():
    """Every claim written so far has none, and a missing level is not the
    same as a low one."""
    assert make_claim(ClaimSource.USER).confidence is None


@pytest.mark.parametrize("level", list(Confidence))
def test_confidence_is_a_level_not_a_number(level):
    """A judgement made in seconds carries no more resolution than this, and a
    float would invite a precision the reader does not have."""
    assert make_claim(ClaimSource.USER, confidence=level).confidence is level


@pytest.mark.parametrize("code", ["", "  ", "../evil", "a/b", "Foo", "-leading-dash"])
def test_technique_code_must_be_a_safe_slug(code):
    with pytest.raises(ValidationError):
        entry(code)


@pytest.mark.parametrize("code", ["monotonic-stack", "backtracking"])
def test_technique_code_accepts_slug(code):
    assert entry(code).code == code


def test_a_self_label_is_its_own_record():
    """A verdict made after the fact and open to revision, like a claim — too
    late to be a field on an append-only attempt."""
    assert "self_label" not in Attempt.model_fields


def test_self_label_roundtrip(tmp_path):
    log = AttemptLog(tmp_path)
    now = datetime.now(UTC)
    first = SelfLabel(id="l1", created_at=now, attempt_id="a1", mode=FailureMode.GAP)
    second = SelfLabel(id="l2", created_at=now, attempt_id="a1", mode=FailureMode.RUST)
    log.append_self_label(first)
    log.append_self_label(second)

    assert log.self_labels() == [first, second]


ATTEMPT_RECORDS = [SelfLabel, TechniqueClaim, Diagnosis]


@pytest.mark.parametrize("record", ATTEMPT_RECORDS)
def test_every_record_keyed_to_an_attempt_shares_the_base(record):
    """One reader serves all three: `latest_by_attempt` needs `attempt_id` and
    `created_at`, and an eval naming what it scored needs `id`."""
    assert issubclass(record, AttemptRecord)
    assert {"id", "created_at", "attempt_id"} <= set(record.model_fields)


@pytest.mark.parametrize("record", ATTEMPT_RECORDS)
def test_an_attempt_record_is_referenceable(record):
    """Identity is required, not optional: a record nothing can name cannot be
    cited by a later one."""
    assert record.model_fields["id"].is_required()


def test_a_self_label_and_a_diagnosis_stay_separate_records():
    """Both answer why an attempt went the way it did, but the eval scores one
    against the other — merged under latest-wins, the machine would supersede
    the ground truth it is measured against."""
    assert "confidence" not in SelfLabel.model_fields
    assert "model" not in SelfLabel.model_fields
