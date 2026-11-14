from climb.ratings.table import difficulty_ratings
from climb.schema import DifficultyRating
from climb.storage import Database, Log


class RatingLog(Log[DifficultyRating]):
    def __init__(self, root: Database) -> None:
        super().__init__(root, difficulty_ratings, DifficultyRating)

    def ratings(self) -> list[DifficultyRating]:
        return self.all()

    def for_problem(self, problem_id: str) -> list[DifficultyRating]:
        return self.where(difficulty_ratings.c.problem_id == problem_id)
