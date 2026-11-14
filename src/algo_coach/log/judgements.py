from algo_coach.log.table import judgements
from algo_coach.schema import Judgement
from algo_coach.storage import Database, Log


class JudgementLog(Log[Judgement]):
    def __init__(self, root: Database) -> None:
        super().__init__(root, judgements, Judgement)

    def for_user(self, user_id: str) -> list[Judgement]:
        return self.where(judgements.c.user_id == user_id)
