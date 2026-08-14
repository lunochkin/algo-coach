import pytest
from pydantic import ValidationError

from algo_coach.schema import Card, ProblemDifficulty, Selector, Template


def template(slug: str = "sliding-window") -> Template:
    return Template(id=f"minted-{slug}", slug=slug, title=slug, code="def f(): pass")


def card(slug: str = "two-pointers-basic", *, technique: str = "two-pointers", **kwargs) -> Card:
    return Card(
        id=f"minted-{slug}",
        slug=slug,
        technique=technique,
        title=slug,
        templates=kwargs.pop("templates", [template()]),
        selector=kwargs.pop("selector", Selector(technique=technique, size=5)),
        **kwargs,
    )


def test_a_card_names_no_problem():
    """The ladder is derived from the corpus, not authored into the card. Ids
    are minted per engine, so a card holding them would mean nothing in another
    store — the selector is what ships."""
    assert card().selector.technique == "two-pointers"
    assert not [name for name in Card.model_fields if "problem" in name]


def test_a_selector_narrows_a_technique_by_named_fields():
    """Difficulty empty is the whole range: an author who says nothing has not
    said "easy". Filters are named fields rather than a map, so what a resolver
    branches on is what the type states."""
    selector = Selector(technique="two-pointers", size=5)
    assert selector.difficulty == []
    assert Selector(
        technique="two-pointers", size=5, difficulty=[ProblemDifficulty.MEDIUM]
    ).difficulty == [ProblemDifficulty.MEDIUM]


def test_a_ladder_of_nothing_teaches_nothing():
    with pytest.raises(ValidationError):
        Selector(technique="two-pointers", size=0)


def test_several_cards_per_technique():
    """Granularity follows teaching, not estimation: mastery is per technique,
    so nothing makes a technique's card unique."""
    first, second = card("two-pointers-basic"), card("two-pointers-on-sorted")
    assert first.technique == second.technique
    assert first.slug != second.slug


def test_a_card_carries_both_identities():
    """The minted id is what a run references; the slug is what a re-import
    matches, so re-seeding refreshes a card rather than minting a second one."""
    assert card().id != card().slug


def test_a_template_carries_both_identities():
    """A recall attempt keys to the minted id and outlives any authoring edit;
    the slug is how a re-import finds the same template to keep it against."""
    assert template().id != template().slug


def test_template_slugs_are_unique_within_a_card():
    """Two templates sharing a slug leave a re-import with no rule for which
    minted id to keep, and a recall history split across both."""
    with pytest.raises(ValidationError):
        card(templates=[template("sliding-window"), template("sliding-window")])


@pytest.mark.parametrize("slug", ["Two-Pointers", "two pointers", "-two-pointers", ""])
def test_a_slug_is_a_stable_lowercase_code(slug):
    """Authored by hand and typed by hand, so the shape is checked where it is
    written rather than where a lookup silently misses."""
    with pytest.raises(ValidationError):
        card(slug)


def test_a_card_needs_something_to_reproduce():
    """A card with no template is a reading list: recall is what it organises."""
    with pytest.raises(ValidationError):
        card(templates=[])


def test_the_vocabulary_is_not_checked_by_the_model():
    """Membership is a write-path check, as it is for a claim. A card seeded
    before a code was retired must stay readable by its own schema."""
    assert card(technique="retired-code").technique == "retired-code"


def test_a_card_round_trips():
    original = card()
    assert Card.model_validate_json(original.model_dump_json()) == original
