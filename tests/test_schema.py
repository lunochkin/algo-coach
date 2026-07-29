from datetime import UTC, datetime

from algo_coach.eval import agreement
from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt, Diagnosis, FailureMode, ProblemRef, TestResult


def make_attempt(id: str, self_label: FailureMode | None) -> Attempt:
    now = datetime.now(UTC)
    return Attempt(
        id=id,
        started_at=now,
        finished_at=now,
        problem=ProblemRef(source="local", problem_id="p1", techniques=["two-pointers"]),
        code="def f(): pass",
        tests=[TestResult(name="t1", passed=False)],
        solved=False,
        time_to_solve_sec=900.0,
        self_label=self_label,
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


def test_agreement_counts_latest_diagnosis_only():
    attempts = [make_attempt("a1", FailureMode.GAP), make_attempt("a2", FailureMode.SPEED)]
    diagnoses = [
        make_diagnosis("a1", FailureMode.RUST),
        make_diagnosis("a1", FailureMode.GAP),
        make_diagnosis("a2", FailureMode.SPEED),
    ]

    report = agreement(attempts, diagnoses)
    assert report.n == 2
    assert report.agree == 2
    assert report.rate == 1.0


def test_agreement_skips_unlabeled():
    attempts = [make_attempt("a1", None)]
    diagnoses = [make_diagnosis("a1", FailureMode.SYNTAX)]

    report = agreement(attempts, diagnoses)
    assert report.n == 0
    assert report.rate == 0.0
