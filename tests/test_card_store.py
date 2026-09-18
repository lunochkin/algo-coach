from algo_coach.cards import CardStore
from algo_coach.schema import Card, Selector, Template, TemplateCase


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


def test_a_template_s_cases_round_trip_in_the_authored_order(database):
    """The trainer runs a recalled form against these, so the order the author
    wrote them in is the order they are read back in."""
    store = CardStore(database)
    cases = [
        TemplateCase(args=[[1, 2, 3], 2], expected=1),
        TemplateCase(args=[[], 7], expected=0),
        TemplateCase(args=[[1], 1], expected=None),
    ]
    held = template("lower-bound", card="basic").model_copy(update={"cases": cases})
    store.put(card("basic").model_copy(update={"templates": [held]}))

    read = store.by_slug("basic")

    assert read is not None
    assert list(read.templates[0].cases) == cases


def test_a_template_carries_no_case_until_one_is_authored(database):
    """`content.md`: a template with no cases is read and never recalled, so a
    card authored before the field keeps working."""
    store = CardStore(database)
    store.put(card("basic"))

    read = store.by_slug("basic")

    assert read is not None and read.templates[0].cases == []


def test_a_re_seed_rewrites_the_cases_it_was_given(database):
    """No record points at a case, so the author's last set stands."""
    store = CardStore(database)
    held = template("lower-bound", card="basic").model_copy(
        update={"cases": [TemplateCase(args=[[1], 1], expected=0)]}
    )
    store.put(card("basic").model_copy(update={"templates": [held]}))

    emptied = held.model_copy(update={"cases": []})
    store.put(card("basic").model_copy(update={"templates": [emptied]}))

    read = store.by_slug("basic")
    assert read is not None and read.templates[0].cases == []
