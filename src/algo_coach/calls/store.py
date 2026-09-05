from pathlib import Path

from algo_coach.schema import Call
from algo_coach.storage import JsonlLog


class CallLog(JsonlLog[Call]):
    """What was asked of a model and what returned. No index by hash: several
    calls can share one prompt."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "calls.jsonl", Call)
        # what this instance appended, so a caller reads its own tail without
        # a megabyte-scale load per problem
        self.appended: list[Call] = []

    def append(self, record: Call) -> None:
        super().append(record)
        self.appended.append(record)
