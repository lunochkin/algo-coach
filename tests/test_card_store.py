from algo_coach.cards import CardStore
from algo_coach.schema import Card, Selector, Template


def template(slug: str, *, card: str) -> Template:
    # minted per template, so two cards' templates of one slug are two rows
    return Template(
        id=f"minted-{card}-{slug}",
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
        templates=[template("lower-bound", card=slug)],
        selector=Selector(technique=technique, size=5),
    )


def test_a_technique_reads_every_card_it_carries_and_no_other(database):
    """Granularity follows teaching, so a technique can carry several cards."""
    store = CardStore(database)
    for one in (card("on-answer"), card("basic"), card("windows", technique="sliding-window")):
        store.put(one)

    assert [one.slug for one in store.for_technique("binary-search")] == ["basic", "on-answer"]


def test_a_re_seed_reorders_templates_and_keeps_their_ids(database):
    """A problem names its template by id, so a card revised in place moves its
    templates rather than minting new ones."""
    store = CardStore(database)
    first, second = template("lower-bound", card="basic"), template("upper-bound", card="basic")
    store.put(card("basic").model_copy(update={"templates": [first, second]}))

    store.put(card("basic").model_copy(update={"templates": [second, first]}))

    assert [one.id for one in store.get("minted-basic").templates] == [second.id, first.id]


def test_a_template_a_re_seed_drops_is_gone(database):
    store = CardStore(database)
    first, second = template("lower-bound", card="basic"), template("upper-bound", card="basic")
    store.put(card("basic").model_copy(update={"templates": [first, second]}))

    store.put(card("basic").model_copy(update={"templates": [second]}))

    assert [one.slug for one in store.get("minted-basic").templates] == ["upper-bound"]
