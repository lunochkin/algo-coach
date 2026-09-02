"""Which core templates the corpus cannot exercise.

A card claims to teach every core form it carries. A form no stored solution
displays is reported, never resolved by another problem: a substitution hides
the gap, and the missing problem is then never written.
"""

import pytest
from matching import PROCEDURE, canonical, card, problem, seeded, template

from algo_coach.matches import core, coverage, uncovered
from algo_coach.mint import generator_match, user_match
from algo_coach.schema import ProblemStatus, RetirementReason, SolutionRole


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
    )


def templates(cards, *slugs: str) -> list[str]:
    """The minted ids of one card's templates, by authored slug."""
    by_slug = {one.slug: one.id for one in cards[0].templates}
    return [by_slug[slug] for slug in slugs]


def missing(cards, problems, solutions, matches) -> list[str]:
    return [one.template_slug for one in uncovered(coverage(cards, problems, solutions, matches))]


def test_the_capstone_and_the_procedure_are_not_core(cards):
    """One is offered on request alone, and the other is displayed by every
    solution its technique reaches."""
    assert [one.slug for one in core(cards[0])] == ["fixed-window", "longest-valid-window"]


def test_an_empty_corpus_reports_every_core_template(cards):
    assert missing(cards, [], [], []) == ["fixed-window", "longest-valid-window"]


def test_a_displayed_form_is_no_gap(cards):
    one = problem("p1", techniques=["sliding-window"])
    solution = canonical("p1")
    [fixed] = templates(cards, "fixed-window")

    assert missing(cards, [one], [solution], [generator_match(fixed, solution.id)]) == [
        "longest-valid-window"
    ]


def test_a_negative_verdict_leaves_the_gap(cards):
    """A pair the matcher answered is read, not merely counted."""
    one = problem("p1", techniques=["sliding-window"])
    solution = canonical("p1")
    [fixed] = templates(cards, "fixed-window")

    read = user_match(fixed, solution.id, matched=False)
    assert "fixed-window" in missing(cards, [one], [solution], [read])


def test_the_standing_verdict_decides(cards):
    """A hand annotation overturning a matcher's positive reopens the gap."""
    one = problem("p1", techniques=["sliding-window"])
    solution = canonical("p1")
    [fixed] = templates(cards, "fixed-window")

    matches = [generator_match(fixed, solution.id), user_match(fixed, solution.id, matched=False)]
    assert "fixed-window" in missing(cards, [one], [solution], matches)


def test_a_retired_problem_fills_no_rung(cards):
    """It is not served, so a form only its canonical displays is still a gap."""
    retired = problem("p1", techniques=["sliding-window"]).model_copy(
        update={
            "status": ProblemStatus.RETIRED,
            "retired_reason": RetirementReason.TELEGRAPHED,
        }
    )
    solution = canonical("p1")
    [fixed] = templates(cards, "fixed-window")

    asserted = generator_match(fixed, solution.id)
    assert "fixed-window" in missing(cards, [retired], [solution], [asserted])


def test_a_reference_displays_nothing(cards):
    """It is written from the statement alone, so it is the naive approach the
    form replaces."""
    one = problem("p1", techniques=["sliding-window"])
    solution = canonical("p1").model_copy(update={"role": SolutionRole.REFERENCE})
    [fixed] = templates(cards, "fixed-window")

    read = user_match(fixed, solution.id, matched=True)
    assert "fixed-window" in missing(cards, [one], [solution], [read])


def test_coverage_names_what_displays_each_form(cards):
    """Two canonicals of one form, so the report says how thin a rung is."""
    problems = [problem(id, techniques=["sliding-window"]) for id in ("p1", "p2")]
    solutions = [canonical("p1"), canonical("p2")]
    [fixed] = templates(cards, "fixed-window")

    covered = coverage(
        cards,
        problems,
        solutions,
        [generator_match(fixed, one.id) for one in solutions],
    )
    assert [(one.template_slug, one.solution_ids) for one in covered] == [
        ("fixed-window", ["s-p1", "s-p2"]),
        ("longest-valid-window", []),
    ]
