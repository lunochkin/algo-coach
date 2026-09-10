from algo_coach.schema import Card


def without_optional(card: Card) -> Card:
    """The card as a sitting shows it. `content.md` gives why the optional
    template is surfaced on request alone."""
    dump = card.model_dump()
    return Card.model_validate(
        dump | {"templates": [one for one in dump["templates"] if not one["optional"]]}
    )
