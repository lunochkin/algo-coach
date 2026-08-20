"""The order a hand annotation is asked in.

The pool is skewed the way the corpus is: three cards on one technique take
every problem tagged with it, and a card on a rare tag takes eleven. What these
check is that a prefix is spread across templates rather than drawn from
whichever card the backlog feeds most.

Levelled on template rather than card, because the score is grouped per
template and the ladder is resolved per template — a form with no annotated
pair is a gap nothing else reports.
"""

from matching import card, problem, seeded, stored, template

from algo_coach.matches import annotatable
from algo_coach.mint import user_match


def corpus(root, *, backtracking: int = 3, union: int = 3):
    """Two cards on different techniques, and problems on each. Enough of both
    that the order has a choice to make at every step."""
    cards = seeded(
        root,
        card(
            "backtracking",
            technique="backtracking",
            templates=[template("subsets"), template("permutations"), template("grid-walk")],
        ),
        card(
            "union-find",
            technique="union-find",
            templates=[template("plain-union"), template("weighted-union")],
        ),
    )
    problems = stored(
        root,
        *(problem(f"b{n}", tags=["Backtracking"]) for n in range(backtracking)),
        *(problem(f"u{n}", tags=["Union Find"]) for n in range(union)),
    )
    return cards, problems


def slugs(cards):
    """Template slug to minted id — what a hand match is written against, and
    what a seed file cannot carry."""
    return {one.slug: one.id for card in cards for one in card.templates}


def test_a_card_the_hand_settled_whole_drops_out(tmp_path):
    """The question asks about the card, so it stands until every template of
    it is settled for that problem. Same rule the run path skips a pair by."""
    cards, problems = corpus(tmp_path)
    id = slugs(cards)
    settled = [
        user_match(id[form], "b0", matched=False)
        for form in ("subsets", "permutations", "grid-walk")
    ]
    order = annotatable(cards, problems, settled)
    assert ("backtracking", "b0") not in {(one.card.slug, one.problem.id) for one in order}


def test_a_card_the_hand_settled_partly_still_asks(tmp_path):
    """A partly annotated card is a question still worth asking — the call
    covers the templates it left, and answering them again settles nothing
    differently."""
    cards, problems = corpus(tmp_path)
    id = slugs(cards)
    part = [user_match(id["subsets"], "b0", matched=True)]
    order = annotatable(cards, problems, part)
    assert ("backtracking", "b0") in {(one.card.slug, one.problem.id) for one in order}


def test_the_least_annotated_template_is_drawn_first(tmp_path):
    """A card whose forms the hand has reached many times waits behind one it
    has never reached."""
    cards, problems = corpus(tmp_path)
    id = slugs(cards)
    ahead = [
        user_match(id[form], f"u{n}", matched=False)
        for form in ("plain-union", "weighted-union")
        for n in range(3)
    ]
    order = annotatable(cards, problems, ahead)
    assert order[0].card.slug == "backtracking"


def test_a_template_nothing_reached_pulls_its_card_forward(tmp_path):
    """What levelling on template catches and levelling on card cannot.

    A re-seeded card gains a form, and its siblings carry forty annotations
    while the new one carries none. Counted per card the card is the best
    covered there is; counted per template it holds the only gap.
    """
    cards, problems = corpus(tmp_path)
    id = slugs(cards)
    lopsided = [
        # Every backtracking problem annotated, but only for two of the three
        # forms — `grid-walk` is the one nothing has reached.
        user_match(id[form], f"b{n}", matched=False)
        for form in ("subsets", "permutations")
        for n in range(3)
    ] + [user_match(id["plain-union"], "u0", matched=False)]
    order = annotatable(cards, problems, lopsided)
    assert order[0].card.slug == "backtracking"


def test_one_card_is_asked_about_alone(tmp_path):
    """Annotating a card just added, without the rest of the corpus in the way.
    The filter narrows what is asked and changes nothing about the order."""
    cards, problems = corpus(tmp_path)
    order = annotatable(cards, problems, [], card="union-find")
    assert {one.card.slug for one in order} == {"union-find"}
    assert {one.problem.id for one in order} == {"u0", "u1", "u2"}


def test_an_unknown_card_asks_nothing(tmp_path):
    cards, problems = corpus(tmp_path)
    assert annotatable(cards, problems, [], card="no-such-card") == []


def test_every_question_is_asked_once(tmp_path):
    """It reorders the pool and never filters it, so a sample cut at any length
    is that length."""
    cards, problems = corpus(tmp_path, backtracking=4, union=4)
    order = annotatable(cards, problems, [])
    assert len(order) == 8
    assert len({one.key for one in order}) == 8


def test_the_same_seed_gives_the_same_order(tmp_path):
    cards, problems = corpus(tmp_path, backtracking=5, union=5)
    assert [one.key for one in annotatable(cards, problems, [], seed=7)] == [
        one.key for one in annotatable(cards, problems, [], seed=7)
    ]


def test_another_seed_gives_another_order(tmp_path):
    """Within a card the choice is the seed's, as a claim sample is described
    by its seed rather than by listing what it held."""
    cards, problems = corpus(tmp_path, backtracking=8, union=8)
    assert [one.key for one in annotatable(cards, problems, [], seed=0)] != [
        one.key for one in annotatable(cards, problems, [], seed=1)
    ]


def test_a_machine_match_does_not_settle_a_question(tmp_path):
    """The hand annotation is what a reading is scored against, so a reading
    never takes its own question out of the pool."""
    from algo_coach.mint import machine_match

    cards, problems = corpus(tmp_path)
    id = slugs(cards)
    read = [
        machine_match(
            id[form],
            "b0",
            matched=False,
            model="m",
            effort="medium",
            prompt_hash="h",
            call_id="c",
            pin="p",
        )
        for form in ("subsets", "permutations", "grid-walk")
    ]
    order = annotatable(cards, problems, read)
    assert ("backtracking", "b0") in {(one.card.slug, one.problem.id) for one in order}


def test_an_empty_corpus_asks_nothing(tmp_path):
    assert annotatable([], [], []) == []
