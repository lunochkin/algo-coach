from pathlib import Path

from algo_coach.schema import TechniqueReading
from algo_coach.storage import JsonlLog


class ReadingLog(JsonlLog[TechniqueReading]):
    """Technique readings, hand and machine alike."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "technique_readings.jsonl", TechniqueReading)

    def readings(self) -> list[TechniqueReading]:
        return self.all()

    def for_solution(self, solution_id: str) -> list[TechniqueReading]:
        return [one for one in self.all() if one.solution_id == solution_id]
