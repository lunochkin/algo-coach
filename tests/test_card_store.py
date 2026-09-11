from algo_coach.cards import CardStore
from algo_coach.schema import Card, Selector, Template


def template(slug: str) -> Template:
    return Template(
        id=f"minted-{slug}",
        slug=slug,
        title=slug,
        trigger="a trigger",
        code="def f(): pass",
    )


def card(slug: str, *, technique: str = "binary-search") -> Card:
    return Card(
        id=f"minted-{slug}",
        slug=slug,
        technique=technique,
        title=slug,
        trigger="a sorted range",
        brief="## Core idea",
        templates=[template("lower-bound")],
        selector=Selector(technique=technique, size=5),
    )


def test_a_technique_reads_every_card_it_carries_and_no_other(database):
    """Granularity follows teaching, so a technique can carry several cards."""
    store = CardStore(database)
    for one in (card("on-answer"), card("basic"), card("windows", technique="sliding-window")):
        store.put(one)

    assert [one.slug for one in store.for_technique("binary-search")] == ["basic", "on-answer"]
