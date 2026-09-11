from algo_coach.schema import SolutionClaim
from algo_coach.solution_claims.table import solution_claims
from algo_coach.storage import Database, Log


class SolutionClaimLog(Log[SolutionClaim]):
    """Solution claims, the user's and the machine's alike."""

    def __init__(self, root: Database) -> None:
        super().__init__(root, solution_claims, SolutionClaim)

    def claims(self) -> list[SolutionClaim]:
        return self.all()

    def for_solution(self, solution_id: str) -> list[SolutionClaim]:
        return self.where(solution_claims.c.solution_id == solution_id)
