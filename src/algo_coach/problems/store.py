from pathlib import Path

from algo_coach.schema import Problem, ProblemStatus, RetirementReason
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

    def retire(self, problem_id: str, reason: RetirementReason) -> Problem:
        stored = self.get(problem_id)
        if stored is None:
            raise ValueError(f"no problem {problem_id}")
        # a sitting asks about each of its attempts in turn, so the second mark
        # on one problem is the loop repeating itself rather than a mistake
        if stored.status is ProblemStatus.RETIRED:
            return stored
        retired = Problem.model_validate(
            stored.model_dump() | {"status": ProblemStatus.RETIRED, "retired_reason": reason}
        )
        self.put(retired)
        return retired
