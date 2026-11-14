import pytest
from generating import FakeWriter
from matching import card, seeded
from pydantic import ValidationError

from climb.calls import CallLog
from climb.drafts import DraftStore
from climb.generation import Corpus, blind, write_problems
from climb.generation.screen import Verdict, prompt
from climb.outcomes import OutcomeLog
from climb.schema import CallSite, DraftCase, Gate, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"


def run(database, model: FakeWriter):
    (one,) = seeded(database, card())
    outcomes, drafts = OutcomeLog(database), DraftStore(database)
    result = write_problems(
        model,
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        outcomes=outcomes,
        drafts=drafts,
    )
    return result, outcomes.outcomes(), drafts.all()


def test_a_copied_draft_is_rejected_before_the_reference(database):
    """A copy then costs the screen's call alone, rather than the four after
    it."""
    model = FakeWriter(generator=BUILDS, copied="a published histogram problem")

    result, _, (draft,) = run(database, model)

    assert result.drafted == []
    assert [one.gate for one in result.rejected] == [Gate.COPIED]
    assert (draft.state, draft.gate) == (WritingState.REJECTED, Gate.COPIED)
    assert blind.SYSTEM not in [asked["system"] for asked in model.calls]


def test_the_screens_record_names_the_published_problem(database):
    """A reader can check the verdict only against the problem it named."""
    _, outcomes, _ = run(database, FakeWriter(generator=BUILDS, copied="a published one"))

    (screened,) = [one for one in outcomes if one.site is CallSite.SCREEN]
    assert screened.gate is Gate.COPIED
    assert "a published one" in screened.detail


def test_nothing_copied_reaches_the_reference(database):
    result, outcomes, _ = run(database, FakeWriter(generator=BUILDS))

    assert len(result.drafted) == 1
    (screened,) = [one for one in outcomes if one.site is CallSite.SCREEN]
    assert (screened.gate, screened.detail) == (None, "")


def test_the_screen_reads_the_statement_and_every_case():
    """A published example reaches a draft as the worked example or as a
    case's arguments."""
    cases = [DraftCase(args=[[2, 1, 5]], expected=5), DraftCase(args=[[]], expected=0)]

    content = prompt("Find the widest stretch.", cases)

    assert "Find the widest stretch." in content
    assert "args=[[2, 1, 5]] expected=5" in content and "args=[[]] expected=0" in content


def test_a_copy_names_where_it_came_from():
    """A verdict naming no published problem cannot be checked by anyone."""
    with pytest.raises(ValidationError):
        Verdict(copied=True, published=None)


def test_the_next_call_is_shown_the_example_a_copy_reused(database):
    """A rejected draft is never stored, so without its screen's verdict the
    next call is sent the same prompt and reproduces the same example."""
    (one,) = seeded(database, card())
    model = FakeWriter(generator=BUILDS, copied="Jump Game II: [2, 3, 1, 1, 4]")

    write_problems(
        model,
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        count=2,
        outcomes=OutcomeLog(database),
        drafts=DraftStore(database),
    )

    first, second = model.prompts
    assert "[2, 3, 1, 1, 4]" not in first
    assert "[2, 3, 1, 1, 4]" in second


def test_a_copy_on_another_template_is_not_shown(database):
    """The examples listed are this form's alone: another form's published
    problem is no likelier to recur here."""
    run(database, FakeWriter(generator=BUILDS, copied="Gas Station: [1, 2, 3, 4, 5]"))
    (one,) = seeded(database, card())
    model = FakeWriter(generator=BUILDS)

    write_problems(
        model,
        CallLog(database),
        one,
        one.templates[1],
        Corpus.at(database),
        outcomes=OutcomeLog(database),
        drafts=DraftStore(database),
    )

    assert "Gas Station" not in model.prompts[0]
