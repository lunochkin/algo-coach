"""What a generation run is aimed at: the core templates carrying no match.

The selector fills a ladder from whatever the corpus holds, so a form nothing
displays is never asked for unless the run names it.
"""

import pytest
from matching import PROCEDURE, canonical, card, problem, seeded, template

from algo_coach.generation import targets
from algo_coach.mint import generator_match


@pytest.fixture
def cards(tmp_path):
    return seeded(
        tmp_path,
        card(
            templates=[
                template("fixed-window"),
                template("longest-valid-window"),
                template("shrink-to-fit", optional=True),
                template("naming-the-invariant", **PROCEDURE),
            ]
        ),
        card(
            "union-find",
            technique="union-find",
            templates=[template("plain-union")],
        ),
    )


def aimed(cards, problems=(), solutions=(), matches=()) -> list[str]:
    return [one.template.slug for one in targets(cards, problems, solutions, matches)]


def test_every_core_template_of_an_empty_corpus(cards):
    assert aimed(cards) == ["fixed-window", "longest-valid-window", "plain-union"]


def test_a_form_the_corpus_displays_is_not_written_again(cards):
    one = problem("p1", techniques=["sliding-window"])
    solution = canonical("p1")
    fixed = next(t.id for t in cards[0].templates if t.slug == "fixed-window")

    assert aimed(cards, [one], [solution], [generator_match(fixed, solution.id)]) == [
        "longest-valid-window",
        "plain-union",
    ]


def test_a_target_carries_the_card_the_brief_is_built_from(cards):
    assert [one.card.slug for one in targets(cards, [], [], [])] == [
        "sliding-window",
        "sliding-window",
        "union-find",
    ]
