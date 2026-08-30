"""Writing several problems for one template: what each call is shown, and
what a failure costs."""

from generating import FakeWriter
from helpers import PROVENANCE
from matching import card, seeded

from algo_coach.calls import CallLog
from algo_coach.generation import write_problems
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Problem


def run(tmp_path, model: FakeWriter, *, count: int = 1, problems=()):
    (one,) = seeded(tmp_path, card())
    return one, write_problems(
        model, CallLog(tmp_path), one, one.templates[0], problems, count=count
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
    corpus = [
        Problem(
            id="p1",
            title="p1",
            statement="An earlier statement.",
            generated_for=one.templates[0].id,
            **PROVENANCE,
        )
    ]
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
