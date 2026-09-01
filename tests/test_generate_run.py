"""Writing several problems for one template: what each call is shown, what a
failure costs, and what the runs reject."""

from generating import FakeWriter
from helpers import PROVENANCE
from matching import card, seeded

from algo_coach.calls import CallLog
from algo_coach.generation import Corpus, write_problems
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import ExpectedSource, Problem


def run(tmp_path, model: FakeWriter, *, count: int = 1):
    (one,) = seeded(tmp_path, card())
    return one, write_problems(
        model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path), count=count
    )


def test_a_problem_takes_two_calls_in_one_order(tmp_path):
    """The reference is written from the statement, so it cannot be asked for
    before there is a statement to test."""
    model = FakeWriter()

    _, result = run(tmp_path, model)

    assert [one["content"].startswith("<problem>") for one in model.calls] == [False, True]
    assert len(result.drafted) == 1
    assert result.drafted[0].solution.startswith("def solve")


def test_each_call_is_shown_what_the_run_wrote_before_it(tmp_path):
    """Added without waiting for the problem to land, or a run of ten writes
    ten problems against one list."""
    model = FakeWriter(statements=["The first.", "The second."])

    run(tmp_path, model, count=2)

    assert "The first." not in model.briefs[0]
    assert "The first." in model.briefs[1]


def test_the_corpus_seeds_the_list(tmp_path):
    """What a form already carries is what the first call has to differ from."""
    (one,) = seeded(tmp_path, card())
    corpus = Corpus.at(tmp_path)
    corpus.problems.put(
        Problem(
            id="p1",
            title="p1",
            statement="An earlier statement.",
            generated_for=one.templates[0].id,
            **PROVENANCE,
        )
    )
    model = FakeWriter()

    write_problems(model, CallLog(tmp_path), one, one.templates[0], corpus)

    assert "An earlier statement." in model.briefs[0]


def test_a_failure_costs_one_problem(tmp_path):
    """A refusal or a reply that does not parse is this problem's, and the run
    behind it still writes."""
    model = FakeWriter(statements=[None, "The second."])

    _, result = run(tmp_path, model, count=2)

    assert [one.index for one in result.failed] == [1]
    assert len(result.drafted) == 1
    assert not result.aborted


def test_several_failures_in_a_row_end_the_run(tmp_path):
    """Consecutive failures mean the configuration is broken rather than the
    model unlucky."""
    model = FakeWriter(statements=[None])

    _, result = run(tmp_path, model, count=ABORT_AFTER + 2)

    assert result.aborted
    assert len(result.failed) == ABORT_AFTER


def test_every_call_is_recorded(tmp_path):
    """Both of them, the failed one included: what a run paid for stays
    readable whatever it produced."""
    model = FakeWriter(statements=[None, "The second."])

    run(tmp_path, model, count=2)

    assert len(CallLog(tmp_path).all()) == 3


def test_a_problem_the_runs_reject_is_reported_apart(tmp_path):
    """A written problem can still be discarded, and a report folding the two
    would say a call refused where the model wrote and the runs rejected."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, result = run(tmp_path, model)

    assert result.drafted == []
    assert result.failed == []
    assert [one.discard for one in result.discarded] == ["disagreed"]
    assert "disagree on 1 case(s)" in result.discarded[0].reason


def test_a_discard_does_not_end_the_run(tmp_path):
    """`ABORT_AFTER` catches a broken configuration. Every call answered here,
    and what the runs rejected is the model's writing."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, result = run(tmp_path, model, count=ABORT_AFTER + 1)

    assert not result.aborted
    assert len(result.discarded) == ABORT_AFTER + 1


def test_a_discarded_statement_is_still_shown_to_the_next_call(tmp_path):
    """It was written for this form, and asking for it again is what the list
    exists to prevent."""
    model = FakeWriter(
        statements=["The first.", "The second."],
        solution="def solve(xs):\n    return len(xs) + 1\n",
    )

    run(tmp_path, model, count=2)

    assert "The first." in model.briefs[1]


def test_a_surviving_problem_carries_what_the_reference_computed(tmp_path):
    """The draft's own values were the gate. What would land is the answer the
    independent solution gave, and the case names it."""
    _, result = run(tmp_path, FakeWriter())

    (drafted,) = result.drafted
    assert [one.expected for one in drafted.cases] == [3]
    assert [one.expected_from for one in drafted.cases] == [ExpectedSource.REFERENCE]
