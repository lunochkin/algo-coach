"""Fixtures the matcher tests share: a model answering from a script, and the
records a verdict needs to exist."""

from helpers import GENERATED, PROVENANCE, T0

from algo_coach.cards import CardStore, seed_cards
from algo_coach.mint import user_reading
from algo_coach.problems import ProblemStore
from algo_coach.readings import ReadingLog
from algo_coach.schema import Card, Problem, Solution, SolutionRole, TemplateKind


def template(slug: str, **overrides) -> dict:
    # its own optimum unless a test says otherwise: a claimed speedup holds the
    # draft where nothing separated, which every landing test would then
    # arrange
    return {
        "slug": slug,
        "title": slug,
        "trigger": f"the cue for {slug}",
        "code": f"def {slug.replace('-', '_')}(): pass",
        "speedup": False,
    } | overrides


def card(
    slug: str = "sliding-window",
    *,
    technique: str = "sliding-window",
    templates: list[dict] | None = None,
    **overrides,
) -> dict:
    return {
        "slug": slug,
        "technique": technique,
        "title": slug,
        "trigger": "a window over a contiguous run",
        "brief": "## Core idea\n\nGrow, then shrink.",
        "templates": templates or [template("longest-valid-window"), template("fixed-window")],
        "selector": {"technique": technique, "size": 5},
    } | overrides


def seeded(root, *records: dict) -> list[Card]:
    """Cards as the engine holds them: minted ids, since a match references
    them and a seed file carries none. In the order authored, not the order
    the store happens to list minted ids in."""
    store = CardStore(root)
    authored = records or (card(),)
    result = seed_cards(authored, store=store)
    assert result.rejected == []
    return [store.by_slug(one["slug"]) for one in authored]


def problem(
    id: str, *, techniques: list[str], statement: str = "Given an array, return ..."
) -> Problem:
    return Problem(
        id=id,
        title=id,
        statement=statement,
        techniques=techniques,
        **GENERATED,
    )


def canonical(problem_id: str, *, id: str | None = None, **overrides) -> Solution:
    """A canonical of one problem, which is what a match is keyed to. Its id
    follows the problem's, so a test naming a pair reads without a lookup."""
    fields = {"code": "def solve(xs):\n    return len(xs)\n"} | overrides
    return Solution(
        id=id or f"s-{problem_id}",
        created_at=T0,
        problem_id=problem_id,
        role=SolutionRole.CANONICAL,
        **PROVENANCE,
        **fields,
    )


def canonicals(*problems: Problem) -> list[Solution]:
    """One canonical each, for a test that cares about the problems rather
    than about which solution answered."""
    return [canonical(one.id) for one in problems]


def stored(root, *problems: Problem) -> list[Problem]:
    """Stored as the engine holds them: the record carries no techniques, and a
    hand reading on the canonical `canonicals()` mints for it carries the ones
    the test named. Returned carrying them, as `load_problems` returns them."""
    store = ProblemStore(root)
    for one in problems:
        store.put(one.model_copy(update={"techniques": []}))
        if one.techniques:
            ReadingLog(root).append(user_reading(f"s-{one.id}", one.techniques))
    return sorted(problems, key=lambda one: one.id)


PROCEDURE = {"kind": TemplateKind.PROCEDURE.value}
