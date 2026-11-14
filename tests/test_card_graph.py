from datetime import timedelta

from helpers import T0
from matching import problem

from climb.cards.graph import depths
from climb.ladder import Rung, met, unmet
from climb.schema import (
    Attempt,
    Card,
    CardRun,
    Probe,
    Requirement,
    Selector,
    Template,
)

TECHNIQUE = "sliding-window"


def built(slug: str, *requires: str) -> Card:
    return Card(
        id=f"c-{slug}",
        slug=slug,
        technique=TECHNIQUE,
        title=slug,
        trigger="the cue",
        brief="## Core idea",
        templates=[Template(id=f"{slug}-form", slug="form", title="form", trigger="x", code="x")],
        selector=Selector(technique=TECHNIQUE, size=1),
        requires=[Requirement(card=one, template="form", used_by="form") for one in requires],
    )


def rung(id: str, *, solved: bool, required: bool = True) -> Rung:
    return Rung(
        problem=problem(id, techniques=[TECHNIQUE]),
        templates=["form"] if required else [],
        required=required,
        solved=solved,
    )


def run(*probes: str) -> CardRun:
    return CardRun(
        id="r-1",
        user_id="u-4f9c2a",
        card_id="c-1",
        started_at=T0,
        probes=[Probe(problem_id=one, assigned_at=T0) for one in probes],
    )


def solve(problem_id: str, *, at=T0 + timedelta(hours=1)) -> Attempt:
    return Attempt(
        id=f"a-{problem_id}",
        user_id="u-4f9c2a",
        problem_id=problem_id,
        finished_at=at,
        solved=True,
    )


def test_a_root_card_has_depth_zero():
    assert depths([built("hashing")]) == {"hashing": 0}


def test_depth_is_the_longest_chain_below_a_card():
    """A card requiring a root and a card one deeper sits two deep."""
    cards = [built("hashing"), built("window", "hashing"), built("deque", "hashing", "window")]

    assert depths(cards) == {"hashing": 0, "window": 1, "deque": 2}


def test_a_card_never_started_is_not_met():
    assert not met(None, [rung("p-1", solved=True)], [])


def test_a_solved_ladder_meets_the_card():
    """The form was reached with the card in view."""
    assert met(run(), [rung("p-1", solved=True), rung("p-2", solved=False, required=False)], [])


def test_an_unsolved_required_rung_leaves_the_card_unmet():
    assert not met(run(), [rung("p-1", solved=False)], [])


def test_a_probe_solved_since_the_run_began_meets_the_card():
    """A user who held the form skips the ladder at the cost of one problem."""
    assert met(run("p-9"), [rung("p-1", solved=False)], [solve("p-9")])


def test_a_probe_solved_before_the_run_began_meets_nothing():
    """The run measures from its start, the probe as the ladder."""
    early = solve("p-9", at=T0 - timedelta(hours=1))

    assert not met(run("p-9"), [rung("p-1", solved=False)], [early])


def test_a_root_card_is_never_locked():
    assert unmet(built("hashing"), set()) == []


def test_a_card_is_locked_until_every_required_card_is_met():
    deque = built("deque", "hashing", "window")

    assert unmet(deque, {"hashing"}) == ["window"]
    assert unmet(deque, {"hashing", "window"}) == []
