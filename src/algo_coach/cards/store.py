from pathlib import Path

from algo_coach.schema import Card


class CardStore:
    """One file per card, named by its engine-minted id.

    A cache of what an author wrote, as the problem store is of what a client
    pushed: a re-seed refreshes the fields and never moves the id, because a
    card run references it.
    """

    def __init__(self, root: Path):
        self.cards_path = root / "cards"

    def put(self, card: Card) -> None:
        self.cards_path.mkdir(parents=True, exist_ok=True)
        path = self.cards_path / f"{card.id}.json"
        path.write_text(card.model_dump_json(indent=2) + "\n")

    def get(self, card_id: str) -> Card | None:
        path = self.cards_path / f"{card_id}.json"
        if not path.exists():
            return None
        return Card.model_validate_json(path.read_text())

    def by_slug(self, slug: str) -> Card | None:
        """Identity across seedings: the same slug is the same card."""
        for card in self.all():
            if card.slug == slug:
                return card
        return None

    def all(self) -> list[Card]:
        if not self.cards_path.exists():
            return []
        return [
            Card.model_validate_json(path.read_text())
            for path in sorted(self.cards_path.glob("*.json"))
        ]
