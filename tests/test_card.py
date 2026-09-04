import pytest
from pydantic import ValidationError

from algo_coach.schema import Card, ProblemDifficulty, Selector, Template, TemplateKind


def template(slug: str = "sliding-window", **kwargs) -> Template:
    return Template(
        id=f"minted-{slug}",
        slug=slug,
        title=slug,
        trigger=kwargs.pop("trigger", "a window over a contiguous run"),
        code=kwargs.pop("code", "def f(): pass"),
        **kwargs,
    )


def card(slug: str = "two-pointers-basic", *, technique: str = "two-pointers", **kwargs) -> Card:
    return Card(
        id=f"minted-{slug}",
        slug=slug,
        technique=technique,
        title=slug,
        trigger=kwargs.pop("trigger", "sorted array, pair summing to a target"),
        brief=kwargs.pop("brief", "## Core idea\n\nTwo indices, one pass."),
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
    matches, so re-seeding refreshes a card rather than minting a second
    one."""
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
    """A card with no template is a reading list: recall is what it
    organises."""
    with pytest.raises(ValidationError):
        card(templates=[])


def test_the_vocabulary_is_not_checked_by_the_model():
    """Membership is a write-path check, as it is for a claim. A card seeded
    before a code was retired must stay readable by its own schema."""
    assert card(technique="retired-code").technique == "retired-code"


def test_the_trigger_is_its_own_field():
    """A probe asks whether the form is recognised unprompted, which is what
    the trigger states — so it is shown and withheld apart from the prose."""
    assert card().trigger not in card().brief


def test_a_template_holds_code_unless_it_says_otherwise():
    """Nearly always code, so that is the default. A method reproduced cold —
    the steps for framing an unseen problem — is the exception that has to say
    so, since nothing else could tell a checklist from source."""
    assert template().kind is TemplateKind.CODE
    steps = template(kind=TemplateKind.PROCEDURE, code="1. State\n2. Meaning\n")
    assert steps.kind is TemplateKind.PROCEDURE


def test_a_template_is_studied_unless_it_says_otherwise():
    """The default is the card's own set. Optional is the capstone a reader
    asks for, so it has to be said."""
    assert template().optional is False


def test_a_card_carries_at_most_one_optional_template():
    """Two optional templates is a second tier of ordinary work wearing the
    name of an exception."""
    with pytest.raises(ValidationError):
        card(templates=[template("a", optional=True), template("b", optional=True)])


def test_a_card_is_not_made_only_of_what_it_withholds():
    """Every template optional means the card teaches nothing until asked."""
    with pytest.raises(ValidationError):
        card(templates=[template("a", optional=True)])
    assert card(templates=[template("a"), template("b", optional=True)])


def test_a_form_that_needs_no_prose_carries_none():
    """The trigger says when the form applies; notes say the rest, where there
    is a rest. A card's brief carries what is technique-wide."""
    assert template().notes is None
    assert template(notes="Absorb the popped span; the entry is its own aggregate.").notes


def test_each_template_states_its_own_cue():
    """Recall is per template, so the cue that has to fire is per template. The
    card's says to reach for the technique; a form's says which form."""
    forms = [template("expanding"), template("fixed-width", trigger="a window of size k")]
    assert len({form.trigger for form in forms}) == 2
    with pytest.raises(ValidationError):
        template(trigger="")


@pytest.mark.parametrize("blank", ["trigger", "brief"])
def test_a_card_says_what_to_read(blank):
    """A card organises what to read as much as what to reproduce. Empty prose
    is not authored prose."""
    with pytest.raises(ValidationError):
        card(**{blank: ""})


def test_a_form_is_a_speedup_unless_it_says_otherwise():
    """Most forms replace a naive solution, so that is the default.
    Backtracking and exhaustive search are their own optimum: no input
    separates them from a reference, and only the template can say so."""
    assert template().speedup is True
    assert template("used-array-permutations", speedup=False).speedup is False


def test_a_card_round_trips():
    original = card()
    assert Card.model_validate_json(original.model_dump_json()) == original
