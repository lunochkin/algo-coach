from pathlib import Path

from algo_coach.schema import Attempt, Diagnosis, SelfLabel, TechniqueClaim
from algo_coach.storage import JsonlLog


class AttemptLog:
    """The private log: attempts, claims, self-labels and diagnoses, one
    append-only file each."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._attempts = JsonlLog(root, "attempts.jsonl", Attempt)
        self._claims = JsonlLog(root, "technique_claims.jsonl", TechniqueClaim)
        self._self_labels = JsonlLog(root, "self_labels.jsonl", SelfLabel)
        self._diagnoses = JsonlLog(root, "diagnoses.jsonl", Diagnosis)

    def append_attempt(self, attempt: Attempt) -> None:
        self._attempts.append(attempt)

    def append_claim(self, claim: TechniqueClaim) -> None:
        self._claims.append(claim)

    def append_self_label(self, label: SelfLabel) -> None:
        self._self_labels.append(label)

    def append_diagnosis(self, diagnosis: Diagnosis) -> None:
        self._diagnoses.append(diagnosis)

    def attempts(self) -> list[Attempt]:
        return self._attempts.all()

    def claims(self) -> list[TechniqueClaim]:
        return self._claims.all()

    def self_labels(self) -> list[SelfLabel]:
        return self._self_labels.all()

    def diagnoses(self) -> list[Diagnosis]:
        return self._diagnoses.all()
