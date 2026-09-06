from pathlib import Path

from algo_coach.schema import Problem
from algo_coach.storage import FileStore

# what a stored problem may still move: `corpus.md` gives the states
STATUS = {"status", "retired_reason"}


class ProblemStore(FileStore[Problem]):
    """Created once; only its status moves. A statement that says the wrong
    thing is retired and a new problem written, so the attempts stay with the
    record they were made against."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "problems", Problem)

    def put(self, record: Problem) -> None:
        if record.techniques:
            # `README.md`: aggregates are derived views, never stored truth
            raise ValueError(f"problem {record.id} carries a view; the store keeps the record")
        stored = self.get(record.id)
        if stored is not None and stored.model_dump(exclude=STATUS) != record.model_dump(
            exclude=STATUS
        ):
            raise ValueError(f"problem {record.id} is stored, and only its status moves")
        super().put(record)
