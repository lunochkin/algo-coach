from algo_coach.outcomes.table import site_outcomes
from algo_coach.schema import SiteOutcome
from algo_coach.storage import Database, Log


class OutcomeLog(Log[SiteOutcome]):
    """What each call site left. A re-run of one site over one item is a second
    record, as a second verification is."""

    def __init__(self, root: Database) -> None:
        super().__init__(root, site_outcomes, SiteOutcome)

    def outcomes(self) -> list[SiteOutcome]:
        return self.all()

    def for_writing(self, writing_id: str) -> list[SiteOutcome]:
        return self.where(site_outcomes.c.writing_id == writing_id)

    def for_problem(self, problem_id: str) -> list[SiteOutcome]:
        return self.where(site_outcomes.c.problem_id == problem_id)
