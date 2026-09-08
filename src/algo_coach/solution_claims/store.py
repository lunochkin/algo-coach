from pathlib import Path

from algo_coach.schema import SolutionClaim
from algo_coach.storage import JsonlLog


class SolutionClaimLog(JsonlLog[SolutionClaim]):
    """Solution claims, hand and machine alike."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "solution_claims.jsonl", SolutionClaim)

    def claims(self) -> list[SolutionClaim]:
        return self.all()

    def for_solution(self, solution_id: str) -> list[SolutionClaim]:
        return [one for one in self.all() if one.solution_id == solution_id]
