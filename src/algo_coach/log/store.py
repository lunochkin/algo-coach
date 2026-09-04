from pathlib import Path

from algo_coach.schema import Attempt, Diagnosis, SelfLabel, TechniqueClaim


class AttemptLog:
    """Append-only JSONL store for attempts, claims, self-labels and
    diagnoses."""

    def __init__(self, root: Path):
        self.root = root
        self.attempts_path = root / "attempts.jsonl"
        self.claims_path = root / "technique_claims.jsonl"
        self.self_labels_path = root / "self_labels.jsonl"
        self.diagnoses_path = root / "diagnoses.jsonl"

    def append_attempt(self, attempt: Attempt) -> None:
        self._append(self.attempts_path, attempt.model_dump_json())

    def append_claim(self, claim: TechniqueClaim) -> None:
        self._append(self.claims_path, claim.model_dump_json())

    def append_self_label(self, label: SelfLabel) -> None:
        self._append(self.self_labels_path, label.model_dump_json())

    def append_diagnosis(self, diagnosis: Diagnosis) -> None:
        self._append(self.diagnoses_path, diagnosis.model_dump_json())

    def attempts(self) -> list[Attempt]:
        return [Attempt.model_validate_json(line) for line in self._lines(self.attempts_path)]

    def claims(self) -> list[TechniqueClaim]:
        return [TechniqueClaim.model_validate_json(line) for line in self._lines(self.claims_path)]

    def self_labels(self) -> list[SelfLabel]:
        return [SelfLabel.model_validate_json(line) for line in self._lines(self.self_labels_path)]

    def diagnoses(self) -> list[Diagnosis]:
        return [Diagnosis.model_validate_json(line) for line in self._lines(self.diagnoses_path)]

    def _append(self, path: Path, line: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(line + "\n")

    @staticmethod
    def _lines(path: Path) -> list[str]:
        if not path.exists():
            return []
        return [line for line in path.read_text().splitlines() if line.strip()]
