from pathlib import Path

from algo_coach.schema import Sitting
from algo_coach.storage import FileStore


class SittingStore(FileStore[Sitting]):
    """Revised as the sitting runs, and kept once it ends: how often practice
    is interrupted is readable here alone."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "sittings", Sitting)

    def running(self, user_id: str, problem_id: str) -> Sitting | None:
        return next(
            (
                one
                for one in self.all()
                if one.user_id == user_id and one.problem_id == problem_id and one.ended_at is None
            ),
            None,
        )
