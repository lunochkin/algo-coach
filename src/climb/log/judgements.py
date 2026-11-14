from climb.log.table import judgements
from climb.schema import Judgement
from climb.storage import Database, Log


class JudgementLog(Log[Judgement]):
    def __init__(self, root: Database) -> None:
        super().__init__(root, judgements, Judgement)

    def for_user(self, user_id: str) -> list[Judgement]:
        return self.where(judgements.c.user_id == user_id)
