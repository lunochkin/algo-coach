from algo_coach.cards import CardStore, without_optional
from algo_coach.schema import Card, Selector, Template


def template(slug: str, *, optional: bool = False) -> Template:
    return Template(
        id=f"minted-{slug}",
        slug=slug,
        title=slug,
        trigger="a trigger",
        code="def f(): pass",
        optional=optional,
    )


def card(slug: str, *, technique: str = "binary-search", templates=None) -> Card:
    return Card(
        id=f"minted-{slug}",
        slug=slug,
        technique=technique,
        title=slug,
        trigger="a sorted range",
        brief="## Core idea",
        templates=templates or [template("lower-bound")],
        selector=Selector(technique=technique, size=5),
    )


def test_a_technique_reads_every_card_it_carries_and_no_other(tmp_path):
    """Granularity follows teaching, so a technique can carry several cards."""
    store = CardStore(tmp_path)
    for one in (card("on-answer"), card("basic"), card("windows", technique="sliding-window")):
        store.put(one)

    assert [one.slug for one in store.for_technique("binary-search")] == ["basic", "on-answer"]


def test_the_optional_template_is_left_off_the_card_a_sitting_shows():
    """`content.md`: the hard form is worth deriving before it is read."""
    shown = without_optional(
        card("basic", templates=[template("core"), template("hard", optional=True)])
    )

    assert [one.slug for one in shown.templates] == ["core"]
