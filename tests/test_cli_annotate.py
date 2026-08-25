"""The hand annotation prompt: one card's templates against one problem.

The question is the card and the record is the pair, so one answer writes a
row per template — the forms the problem does not exercise included, since a
reference that only named matches would score the matcher's "yes" and say
nothing about its "no".

Driven through the pilot rather than the terminal. What is asked and what is
written are the command's, so a sitting can be run headless and the screen is
read back off the widgets.
"""

import argparse
from contextlib import asynccontextmanager

import pytest
from matching import PROCEDURE, card, problem, seeded, stored, template
from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static

from algo_coach.cards import CardStore
from algo_coach.cli.annotate import annotating
from algo_coach.matches import MatchLog
from algo_coach.mint import machine_match
from algo_coach.schema import MatchSource

# Wide and tall: the layout is two panes, and the pilot's default is one
# eighty-column screen. Nothing here asserts on wrapping.
SCREEN = (200, 50)


@pytest.fixture
def annotate_root(tmp_path, monkeypatch):
    """One card of three forms and two problems its technique reaches, plus a
    second card nothing asks about unless `--card` says so."""
    root = tmp_path / "data"
    seeded(
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
    stored(
        root,
        problem("b0", techniques=["backtracking"]),
        problem("b1", techniques=["backtracking"]),
        problem("u0", techniques=["union-find"]),
    )
    return root


def built(root, **flags):
    """The prompt the command builds, before anything runs it."""
    args = argparse.Namespace(**{"count": 10, "card": None, "seed": 0, "verdict": False, **flags})
    return annotating(args, argparse.ArgumentParser(prog="annotate"), root)


@asynccontextmanager
async def sitting(root, presses: list[str], **flags):
    """A sitting, keystroke by keystroke, held open at the last one.

    Yielded from inside the pilot, since a screen can only be read while the
    app is mounted. The app closes itself once the pool runs out, so anything
    left unpressed after that is not sent.
    """
    app = built(root, **flags)
    async with app.run_test(size=SCREEN) as pilot:
        for key in presses:
            if not app.is_running:
                break
            await pilot.press(key)
        yield app
        if app.is_running:
            app.exit()


async def run(root, presses: list[str], **flags) -> None:
    """The same, for a test that reads the log rather than the screen."""
    async with sitting(root, presses, **flags):
        pass


def written(root):
    return MatchLog(root).matches()


def annotated(root):
    """The hand records alone: a test that seeds a matcher's verdict finds it
    in the log beside what the sitting wrote."""
    return [one for one in written(root) if one.source is MatchSource.USER]


def by_slug(root):
    """Minted template id to slug, since a record carries the id and a test
    reads the form."""
    return {one.id: one.slug for card in CardStore(root).all() for one in card.templates}


def read_by_matcher(root):
    """A verdict on `subsets` for every backtracking problem, so whichever the
    order draws first has one to show. Seeded on both, or the test passes by
    drawing the problem nothing read."""
    subsets = next(id for id, name in by_slug(root).items() if name == "subsets")
    for problem_id in ("b0", "b1"):
        MatchLog(root).append(
            machine_match(
                subsets,
                problem_id,
                matched=True,
                model="a-matcher",
                effort="medium",
                prompt_hash="h",
                call_id="c",
                pin="p",
            )
        )


def screen(app, selector: str) -> str:
    return str(app.query_one(selector, Static).content)


async def test_one_answer_writes_a_record_per_template(annotate_root):
    """The picked forms positive and the rest negative, in one write: reading
    a statement once to judge three forms is what the question is for."""
    await run(annotate_root, ["space", "enter"], count=1, card="backtracking")

    slug = by_slug(annotate_root)
    recorded = {slug[one.template_id]: one.matched for one in annotated(annotate_root)}
    assert recorded == {"subsets": True, "permutations": False, "grid-walk": False}


async def test_several_forms_can_be_named(annotate_root):
    """Two approaches to one problem is the ordinary case, and it is what lets
    a rung cover a studied template and an optional one at once."""
    await run(annotate_root, ["space", "3", "space", "enter"], count=1, card="backtracking")

    slug = by_slug(annotate_root)
    recorded = {slug[one.template_id]: one.matched for one in annotated(annotate_root)}
    assert recorded == {"subsets": True, "permutations": False, "grid-walk": True}


async def test_a_pick_can_be_taken_back(annotate_root):
    """The same key both ways, since deciding against a form after reading its
    code is the ordinary case rather than a correction."""
    await run(annotate_root, ["space", "space", "enter"], count=1, card="backtracking")

    assert not any(one.matched for one in annotated(annotate_root))


async def test_naming_none_is_negatives_not_a_decline(annotate_root):
    """A call naming no template asserts that each of them does not match,
    which is a verdict on every pair. The record shape decides that, so the
    prompt has to be able to say it."""
    await run(annotate_root, ["enter"], count=1, card="backtracking")

    recorded = annotated(annotate_root)
    assert len(recorded) == 3
    assert not any(one.matched for one in recorded)


async def test_a_hand_record_carries_no_configuration(annotate_root):
    """Nothing re-derives it, which is what makes it the reference a reading is
    scored against."""
    await run(annotate_root, ["space", "enter"], count=1, card="backtracking")

    one = annotated(annotate_root)[0]
    assert one.source is MatchSource.USER
    assert (one.model, one.pin, one.prompt_hash, one.call_id) == (None, None, None, None)


async def test_a_skip_writes_nothing_and_moves_on(annotate_root):
    """Not the same as recording no template: the pair stays in the pool, so
    a sitting that could not decide costs the reference nothing."""
    await run(annotate_root, ["s", "space", "enter"], count=2, card="backtracking")

    assert len({one.problem_id for one in annotated(annotate_root)}) == 1


async def test_ending_the_sitting_keeps_what_landed(annotate_root):
    """The log is append-only either way, so stopping early costs nothing that
    was answered."""
    await run(annotate_root, ["space", "enter", "q"], count=2, card="backtracking")

    assert len(annotated(annotate_root)) == 3


async def test_the_statement_is_what_is_read(annotate_root):
    """Which form a problem exercises is a question about what it asks, so the
    statement is shown rather than the tags."""
    async with sitting(annotate_root, [], count=1, card="backtracking") as app:
        assert app.query_one("#statement-body", Markdown).source == "Given an array, return ..."


async def test_each_form_is_offered_by_its_own_cue(annotate_root):
    """A template's trigger says which of the technique's forms this is, which
    is exactly what the annotator is deciding."""
    async with sitting(annotate_root, [], count=1, card="backtracking") as app:
        listing = screen(app, "#forms")
        assert "the cue for subsets" in listing
        assert "grid-walk" in listing


async def test_the_form_in_view_shows_its_code(annotate_root):
    """What has to be reproduced is what says whether a problem exercises the
    form. A cue names it; the code is what the annotator reads it against."""
    async with sitting(annotate_root, ["2"], count=1, card="backtracking") as app:
        assert app.query_one("#code-body", Static).content.code == "def permutations(): pass"
        assert "the cue for permutations" in screen(app, "#cue")


async def test_one_form_is_in_view_at_a_time(annotate_root):
    """Six forms run to a hundred and thirty lines of code, which no pane
    holds. Which one is in view is the question already being answered."""
    async with sitting(annotate_root, ["3"], count=1, card="backtracking") as app:
        assert app.query_one("#code-body", Static).content.code == "def grid_walk(): pass"


async def test_neither_pane_takes_focus(annotate_root):
    """A focused scrollable claims space for a page down, and space is how a
    form is picked. Both panes scroll by key and by wheel without it."""
    async with sitting(annotate_root, [], count=1, card="backtracking") as app:
        assert not any(pane.can_focus for pane in app.query(VerticalScroll))


async def test_a_procedure_template_is_never_offered(annotate_root):
    """A framing procedure is exercised by every problem its technique reaches,
    so a per-problem verdict on it carries no information."""
    root = annotate_root
    seeded(
        root,
        card(
            "monotonic-stack",
            technique="monotonic-stack",
            templates=[template("next-greater"), template("framing", **PROCEDURE)],
        ),
    )
    stored(root, problem("m0", techniques=["monotonic-stack"]))
    await run(root, ["space", "enter"], count=1, card="monotonic-stack")

    slug = by_slug(root)
    assert {slug[one.template_id] for one in annotated(root)} == {"next-greater"}


async def test_the_matcher_is_not_shown_by_default(annotate_root):
    """Blind, or the annotation records what it reviewed rather than what it
    read: the first hand pass is what the line gets drawn by."""
    read_by_matcher(annotate_root)
    async with sitting(annotate_root, [], count=1, card="backtracking") as app:
        assert "a-matcher" not in screen(app, "#cue")


async def test_the_matcher_is_shown_on_request(annotate_root):
    """Asked for by name, as `claim --revise` shows a reading — and what it
    costs is that the answer is no longer independent of it."""
    read_by_matcher(annotate_root)
    async with sitting(annotate_root, [], count=1, card="backtracking", verdict=True) as app:
        cue = screen(app, "#cue")
        assert "a-matcher" in cue
        assert "yes" in cue


async def test_a_blind_annotation_names_no_reading(annotate_root):
    """Nothing was in view, so there is nothing to record — which is what makes
    the record independent of every configuration scored against it."""
    read_by_matcher(annotate_root)
    await run(annotate_root, ["enter"], count=1, card="backtracking")

    assert all(one.informed_by == [] for one in annotated(annotate_root))


async def test_an_annotation_records_the_calls_it_saw(annotate_root):
    """On every pair the answer writes, negatives included: what the reader saw
    is a fact about the sitting rather than about the verdict."""
    read_by_matcher(annotate_root)
    await run(annotate_root, ["enter"], count=1, card="backtracking", verdict=True)

    assert all(one.informed_by == ["c"] for one in annotated(annotate_root))


async def test_a_form_no_matcher_read_informs_nothing(annotate_root):
    """Only `subsets` was read, so only its call is named — the other two forms
    were shown with no verdict beside them."""
    read_by_matcher(annotate_root)
    await run(annotate_root, ["space", "enter"], count=1, card="backtracking", verdict=True)

    assert {tuple(one.informed_by) for one in annotated(annotate_root)} == {("c",)}


async def test_one_card_is_asked_about_alone(annotate_root):
    await run(annotate_root, ["enter"], count=1, card="union-find")

    slug = by_slug(annotate_root)
    assert {slug[one.template_id] for one in annotated(annotate_root)} == {
        "plain-union",
        "weighted-union",
    }


def test_an_unseeded_card_is_refused(annotate_root):
    with pytest.raises(SystemExit) as exit:
        built(annotate_root, card="no-such-card")
    assert exit.value.code == 2


async def test_nothing_left_to_annotate_says_so(annotate_root):
    await run(annotate_root, ["enter", "enter"], card="union-find")
    with pytest.raises(SystemExit) as exit:
        built(annotate_root, card="union-find")
    assert exit.value.code == 1
