from pathlib import Path

from algo_coach.schema import TechniqueReading


class ReadingLog:
    """Append-only JSONL store for technique readings, hand and machine
    alike."""

    def __init__(self, root: Path):
        self.root = root
        self.readings_path = root / "technique_readings.jsonl"

    def append(self, reading: TechniqueReading) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.readings_path.open("a") as f:
            f.write(reading.model_dump_json() + "\n")

    def readings(self) -> list[TechniqueReading]:
        if not self.readings_path.exists():
            return []
        return [
            TechniqueReading.model_validate_json(line)
            for line in self.readings_path.read_text().splitlines()
            if line.strip()
        ]

    def for_solution(self, solution_id: str) -> list[TechniqueReading]:
        return [one for one in self.readings() if one.solution_id == solution_id]
