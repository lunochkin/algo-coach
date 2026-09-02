from pathlib import Path

from algo_coach.schema import Verification


class VerificationLog:
    """Append-only JSONL store for verification runs; neither of two runs of
    one solution supersedes the other."""

    def __init__(self, root: Path):
        self.root = root
        self.verifications_path = root / "verifications.jsonl"

    def append(self, verification: Verification) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.verifications_path.open("a") as f:
            f.write(verification.model_dump_json() + "\n")

    def verifications(self) -> list[Verification]:
        if not self.verifications_path.exists():
            return []
        return [
            Verification.model_validate_json(line)
            for line in self.verifications_path.read_text().splitlines()
            if line.strip()
        ]

    def for_solution(self, solution_id: str) -> list[Verification]:
        return [one for one in self.verifications() if one.solution_id == solution_id]
