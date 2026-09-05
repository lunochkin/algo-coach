from pathlib import Path

from algo_coach.schema import Card
from algo_coach.storage import FileStore


class CardStore(FileStore[Card]):
    def __init__(self, root: Path) -> None:
        super().__init__(root, "cards", Card)

    def by_slug(self, slug: str) -> Card | None:
        return next((card for card in self.all() if card.slug == slug), None)
