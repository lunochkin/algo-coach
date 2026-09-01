from pathlib import Path

from algo_coach.schema import TechniqueReading


class ReadingLog:
    """Append-only JSONL store for the technique readings of a solution.

    Re-derivation is the normal path: a criteria edit changes the digest of
    what a reading was sent, and the re-run's verdict lands beside the earlier
    one rather than over it. Which of them stands is the record's question —
    the user's over any machine reading, however late that one was written.

    One store for both writers, as the match log holds one for three. A hand
    reading is what a configuration is scored against, so splitting it out
    would put the reference and the reading being measured in two files that
    every reader joins.
    """

    def __init__(self, root: Path):
        self.root = root
        self.readings_path = root / "technique_readings.jsonl"

    def append(self, reading: TechniqueReading) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.readings_path.open("a") as f:
            f.write(reading.model_dump_json() + "\n")

    def readings(self) -> list[TechniqueReading]:
        """In append order: a tie on `created_at` is broken by what landed last."""
        if not self.readings_path.exists():
            return []
        return [
            TechniqueReading.model_validate_json(line)
            for line in self.readings_path.read_text().splitlines()
            if line.strip()
        ]

    def for_solution(self, solution_id: str) -> list[TechniqueReading]:
        """Every reading of one solution, oldest first. A problem's techniques
        are folded from the readings of its canonicals, so this is the unit
        that fold reads."""
        return [one for one in self.readings() if one.solution_id == solution_id]
