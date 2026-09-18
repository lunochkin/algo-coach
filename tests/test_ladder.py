from datetime import datetime

from helpers import T0
from matching import canonical, card, problem, seeded, template

from algo_coach.ladder import ladder
from algo_coach.mint import generator_match, user_match
from algo_coach.schema import Attempt, ProblemDifficulty, ProblemStatus, RetirementReason

TECHNIQUE = "sliding-window"


def a_card(root, size: int = 5, optional: bool = False, **overrides):
    """One card with two core templates, and the optional one where a test
    asks for it."""
    (held,) = seeded(
        root,
        card(
            templates=[
                template("longest-valid-window"),
                template("fixed-window"),
                *([template("shrink-to-fit", optional=True)] if optional else []),
            ],
            selector={"technique": TECHNIQUE, "size": size} | overrides.pop("selector", {}),
            **overrides,
        ),
    )
    return held


def attempted(problem_id: str, *, at: datetime = T0, id: str | None = None) -> Attempt:
    return Attempt(
        id=id or f"a-{problem_id}",
        user_id="u-4f9c2a",
        problem_id=problem_id,
        finished_at=at,
        solved=True,
    )


def test_a_rung_per_core_template_in_the_card_s_order(database):
    """The card authors its templates in the order it teaches them, so a rung
    covering the first comes before a rung covering the second."""
    held = a_card(database)
    first, second = held.templates[0], held.templates[1]
    problems = [problem("p-2", techniques=[TECHNIQUE]), problem("p-1", techniques=[TECHNIQUE])]
    solutions = [canonical("p-1"), canonical("p-2")]
    matches = [generator_match(first.id, "s-p-2"), generator_match(second.id, "s-p-1")]

    resolved = ladder(held, problems, solutions, matches, [])

    assert [one.problem.id for one in resolved.rungs[:2]] == ["p-2", "p-1"]
    assert [one.templates for one in resolved.rungs[:2]] == [[first.id], [second.id]]


def test_one_problem_covering_two_templates_is_one_rung(database):
    """A rung names every core template its canonicals display, and
    requiredness is derived from that set."""
    held = a_card(database)
    problems = [problem("p-1", techniques=[TECHNIQUE])]
    solutions = [canonical("p-1")]
    matches = [generator_match(one.id, "s-p-1") for one in held.templates]

    resolved = ladder(held, problems, solutions, matches, [])

    assert len(resolved.rungs) == 1
    assert resolved.rungs[0].templates == [one.id for one in held.templates]


def test_the_selector_fills_the_ladder_out_to_size(database):
    """The covering rungs teach the forms, and the selector fills the rest so
    the card has a ladder rather than a pair of problems."""
    held = a_card(database, size=3)
    problems = [problem(f"p-{one}", techniques=[TECHNIQUE]) for one in range(5)]
    solutions = [canonical("p-0")]
    matches = [generator_match(held.templates[0].id, "s-p-0")]

    resolved = ladder(held, problems, solutions, matches, [])

    assert len(resolved.rungs) == 3
    assert resolved.rungs[0].problem.id == "p-0"
    assert [one.templates for one in resolved.rungs[1:]] == [[], []]


def test_the_fill_is_least_recently_attempted_first(database):
    """A technique's candidates are ordered that way, and a ladder draws from
    the same list."""
    held = a_card(database, size=2)
    problems = [problem("p-old", techniques=[TECHNIQUE]), problem("p-new", techniques=[TECHNIQUE])]
    attempts = [
        attempted("p-old", at=datetime.fromisoformat("2026-01-01T00:00:00Z")),
        attempted("p-new", at=datetime.fromisoformat("2026-09-01T00:00:00Z")),
    ]

    resolved = ladder(held, problems, [], [], attempts)

    assert [one.problem.id for one in resolved.rungs] == ["p-old", "p-new"]


def test_a_retired_problem_fills_no_rung(database):
    """A defective problem was never a fair test, so it neither covers a
    template nor fills the ladder out."""
    held = a_card(database, size=3)
    retired = problem("p-retired", techniques=[TECHNIQUE]).model_copy(
        update={"status": ProblemStatus.RETIRED, "retired_reason": RetirementReason.DEFECTIVE}
    )
    problems = [retired, problem("p-live", techniques=[TECHNIQUE])]
    solutions = [canonical("p-retired"), canonical("p-live")]
    matches = [generator_match(held.templates[0].id, "s-p-retired")]

    resolved = ladder(held, problems, solutions, matches, [])

    assert [one.problem.id for one in resolved.rungs] == ["p-live"]
    # the retired problem's canonical displayed the first form, and displays
    # nothing once the problem is out of the corpus
    assert resolved.gaps == ["longest-valid-window", "fixed-window"]


def test_a_core_template_nothing_displays_is_a_gap(database):
    """The ladder never substitutes another problem: a substitution hides the
    gap, and the missing problem is then never written."""
    held = a_card(database, size=2)
    problems = [problem("p-1", techniques=[TECHNIQUE]), problem("p-2", techniques=[TECHNIQUE])]
    solutions = [canonical("p-1")]
    matches = [generator_match(held.templates[1].id, "s-p-1")]

    resolved = ladder(held, problems, solutions, matches, [])

    assert resolved.gaps == ["longest-valid-window"]
    assert resolved.rungs[0].problem.id == "p-1"


def test_the_selector_s_difficulty_narrows_the_fill(database):
    """The selector says what to draw from, and a filter it carries is part of
    that."""
    held = a_card(database, size=2, selector={"difficulty": [ProblemDifficulty.HARD.value]})
    problems = [
        problem("p-easy", techniques=[TECHNIQUE]).model_copy(update={"difficulty": "easy"}),
        problem("p-hard", techniques=[TECHNIQUE]).model_copy(update={"difficulty": "hard"}),
    ]

    resolved = ladder(held, problems, [], [], [])

    assert [one.problem.id for one in resolved.rungs] == ["p-hard"]


def test_a_user_match_stands_over_the_generator_s(database):
    """The ladder reads the verdict that stands on a pair, as every other
    reader of the matches does."""
    held = a_card(database)
    problems = [problem("p-1", techniques=[TECHNIQUE])]
    solutions = [canonical("p-1")]
    matches = [
        generator_match(held.templates[0].id, "s-p-1"),
        user_match(held.templates[0].id, "s-p-1", matched=False),
    ]

    resolved = ladder(held, problems, solutions, matches, [])

    assert resolved.gaps == [one.slug for one in held.templates]
    assert [one.templates for one in resolved.rungs] == [[]]


def test_a_rung_covering_a_core_template_is_required(database):
    """The card claims to teach the form, so the rung that teaches it is not
    a suggestion."""
    held = a_card(database, size=1)
    problems = [problem("p-1", techniques=[TECHNIQUE])]
    matches = [generator_match(held.templates[0].id, "s-p-1")]

    resolved = ladder(held, problems, [canonical("p-1")], matches, [])

    assert [(one.problem.id, one.required) for one in resolved.rungs] == [("p-1", True)]


def test_a_rung_covering_the_optional_template_alone_is_optional(database):
    """A card is covered without its optional template, so the rung that
    teaches that form alone is a stretch rather than the day's work."""
    held = a_card(database, size=1, optional=True)
    problems = [problem("p-1", techniques=[TECHNIQUE]), problem("p-2", techniques=[TECHNIQUE])]
    solutions = [canonical("p-1"), canonical("p-2")]
    matches = [
        generator_match(held.templates[0].id, "s-p-1"),
        generator_match(held.templates[2].id, "s-p-2"),
    ]

    resolved = ladder(held, problems, solutions, matches, [])

    assert [(one.problem.id, one.required) for one in resolved.rungs] == [
        ("p-1", True),
        ("p-2", False),
    ]


def test_a_rung_covering_both_is_required_and_offers_the_alternative(database):
    """One problem two forms solve is one rung, required for the core form,
    with the optional form offered as the other approach."""
    held = a_card(database, size=1, optional=True)
    problems = [problem("p-1", techniques=[TECHNIQUE])]
    matches = [generator_match(one.id, "s-p-1") for one in (held.templates[0], held.templates[2])]

    resolved = ladder(held, problems, [canonical("p-1")], matches, [])

    (rung,) = resolved.rungs
    assert rung.required
    assert rung.templates == [held.templates[0].id, held.templates[2].id]


def test_a_fill_rung_is_optional(database):
    """The selector's fill exercises the technique and teaches no form of it,
    so nothing on the card requires it."""
    held = a_card(database, size=2)
    problems = [problem("p-1", techniques=[TECHNIQUE]), problem("p-2", techniques=[TECHNIQUE])]
    matches = [generator_match(held.templates[0].id, "s-p-1")]

    resolved = ladder(held, problems, [canonical("p-1")], matches, [])

    assert [(one.problem.id, one.required) for one in resolved.rungs] == [
        ("p-1", True),
        ("p-2", False),
    ]


def test_the_optional_template_is_no_gap(database):
    """The gap report skips it: a card is covered without it, and no
    generation run is aimed at it."""
    held = a_card(database, size=1, optional=True)
    problems = [problem("p-1", techniques=[TECHNIQUE])]
    matches = [generator_match(one.id, "s-p-1") for one in held.templates[:2]]

    resolved = ladder(held, problems, [canonical("p-1")], matches, [])

    assert resolved.gaps == []
