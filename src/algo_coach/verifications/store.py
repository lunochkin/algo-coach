from pathlib import Path

from algo_coach.schema import Verification


class VerificationLog:
    """Append-only JSONL store for verification runs.

    Re-running is legal and expected, as re-deriving a reading is. Two runs of
    one solution are two records and neither supersedes the other, so this
    appends and never rewrites. Which run answers a question is the reader's
    to decide, since a run under a different cap answers a different one.
    """

    def __init__(self, root: Path):
        self.root = root
        self.verifications_path = root / "verifications.jsonl"

    def append(self, verification: Verification) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.verifications_path.open("a") as f:
            f.write(verification.model_dump_json() + "\n")

    def verifications(self) -> list[Verification]:
        """In append order: a tie on `created_at` is broken by what landed last."""
        if not self.verifications_path.exists():
            return []
        return [
            Verification.model_validate_json(line)
            for line in self.verifications_path.read_text().splitlines()
            if line.strip()
        ]

    def for_solution(self, solution_id: str) -> list[Verification]:
        """Every run of one solution, oldest first. Nothing lands until a
        solution passes, so what a reader usually wants is whether one of
        these verified rather than which came last."""
        return [one for one in self.verifications() if one.solution_id == solution_id]
