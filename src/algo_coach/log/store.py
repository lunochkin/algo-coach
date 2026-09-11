from pathlib import Path

from algo_coach.schema import Attempt, AttemptClaim, AttemptVerification, Diagnosis, SelfLabel
from algo_coach.storage import Database, JsonlLog


class AttemptLog:
    """The private log: attempts, their verifications, claims, self-labels and
    diagnoses, one append-only file each."""

    def __init__(self, root: Database | Path) -> None:
        self.root = root
        self._attempts = JsonlLog(root, "attempts.jsonl", Attempt)
        self._verifications = JsonlLog(root, "attempt_verifications.jsonl", AttemptVerification)
        self._claims = JsonlLog(root, "attempt_claims.jsonl", AttemptClaim)
        self._self_labels = JsonlLog(root, "self_labels.jsonl", SelfLabel)
        self._diagnoses = JsonlLog(root, "diagnoses.jsonl", Diagnosis)

    def append_attempt(self, attempt: Attempt) -> None:
        self._attempts.append(attempt)

    def append_verification(self, verification: AttemptVerification) -> None:
        self._verifications.append(verification)

    def append_claim(self, claim: AttemptClaim) -> None:
        self._claims.append(claim)

    def append_self_label(self, label: SelfLabel) -> None:
        self._self_labels.append(label)

    def append_diagnosis(self, diagnosis: Diagnosis) -> None:
        self._diagnoses.append(diagnosis)

    def attempts(self) -> list[Attempt]:
        return self._attempts.all()

    def verifications(self) -> list[AttemptVerification]:
        return self._verifications.all()

    def claims(self) -> list[AttemptClaim]:
        return self._claims.all()

    def self_labels(self) -> list[SelfLabel]:
        return self._self_labels.all()

    def diagnoses(self) -> list[Diagnosis]:
        return self._diagnoses.all()
