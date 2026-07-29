from pathlib import Path

from algo_coach.cards.card import Card


class CardStore:
    """Store for cards. One file per card."""

    def __init__(self, root: Path):
        self.cards_path = root / "cards"

    def create_card(self, card: Card) -> None:
        self.cards_path.mkdir(parents=True, exist_ok=True)
        path = self.cards_path / f"{card.name}.json"
        with path.open("x") as f:
            f.write(card.model_dump_json(indent=2) + "\n")
