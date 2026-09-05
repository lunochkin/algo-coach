from pathlib import Path

from algo_coach.schema import Problem
from algo_coach.storage import FileStore


class ProblemStore(FileStore[Problem]):
    def __init__(self, root: Path) -> None:
        super().__init__(root, "problems", Problem)
