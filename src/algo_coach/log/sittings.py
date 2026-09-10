from pathlib import Path

from algo_coach.schema import Sitting
from algo_coach.storage import FileStore


class SittingStore(FileStore[Sitting]):
    """Revised as the sitting runs, and kept once it ends: how often practice
    is interrupted is readable here alone."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "sittings", Sitting)
