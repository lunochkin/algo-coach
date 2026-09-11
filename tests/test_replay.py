from generating import FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog
from algo_coach.cases import CaseLog
from algo_coach.generation import REPLAYED, Bench, Corpus, naive, replay, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    CallSite,
    Configuration,
    Gate,
    ProblemStatus,
    RetirementReason,
    SolutionRole,
)
from algo_coach.solutions import SolutionLog

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# slow enough to separate at the cap the tests lower: a reference the search
# cannot leave behind holds the draft rather than landing it
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]


def landed(database, monkeypatch, model: FakeWriter | None = None, **overrides):
    """One stored problem, written by a run that recorded no outcome of its
    own, so a replay's store starts empty.

    Over a template claiming a speedup, since that is what the inputs site is
    asked about. A run under the real sitting cap holds the draft instead: the
    reference finishes at every size the input generator writes.
    """
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    overrides.setdefault(
        "templates", [template("longest-valid-window", speedup=True), template("fixed-window")]
    )
    (one,) = seeded(database, card(**overrides))
    write_problems(
        model or FakeWriter(slow=SLOW, generator=BUILDS),
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
    )
    return [one]


def replayed(database, model: FakeWriter, cards, *, log=None, **kw):
    log = log or OutcomeLog(database)
    result = replay(model, CallLog(database), Corpus.at(database), log, cards, **kw)
    return result, log.outcomes()


def sites(outcomes) -> dict[CallSite, object]:
    return {one.site: one for one in outcomes}


def test_a_replay_asks_the_answering_sites_about_a_stored_problem(database, monkeypatch):
    """Generation writes a new problem every time, so a configuration is
    compared with another only over a statement that already exists."""
    cards = landed(database, monkeypatch)

    result, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards)

    assert set(sites(outcomes)) == {CallSite.BLIND, CallSite.INPUTS, CallSite.NAIVE}
    assert result.asked == 3


def test_the_search_measures_against_the_stored_naive_solution(database, monkeypatch):
    """The naive solution site answers for itself. A search measured against
    what it just wrote would move two configurations at once, and neither could
    be read."""
    cards = landed(database, monkeypatch)
    # a naive solution that crashes where the stored one runs: a search timing
    # the new one would report `naive_crashed`, where the stored one separates
    model = FakeWriter(generator=BUILDS, slow="def solve(xs):\n    raise ValueError(1)\n")

    _, outcomes = replayed(database, model, cards)

    assert naive.SYSTEM in [asked["system"] for asked in model.calls]
    one = sites(outcomes)[CallSite.INPUTS]
    assert (one.separating, one.unseparated) == (2, None)
    (stored,) = SolutionLog(database).for_problem(
        ProblemStore(database).all()[0].id, SolutionRole.NAIVE
    )
    assert stored.code == SLOW


def test_a_replayed_input_generator_records_the_bound_it_reported(database, monkeypatch):
    """The bound is this call's own answer, and what the search it fed is read
    against."""
    cards = landed(database, monkeypatch)

    _, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards)

    assert sites(outcomes)[CallSite.INPUTS].largest == 8


def test_a_replayed_naive_solution_that_answers_wrongly_names_no_gate(database, monkeypatch):
    """Being wrong rejects no draft, and every `Gate` arm says one was
    rejected. What the record carries is what the run saw."""
    cards = landed(database, monkeypatch)
    wrong = "def solve(xs):\n    return len(xs) + 1\n"

    _, outcomes = replayed(database, FakeWriter(generator=BUILDS, slow=wrong), cards)

    one = sites(outcomes)[CallSite.NAIVE]
    assert one.gate is None
    assert one.detail == "wrong on 2 case(s)"


def test_a_problem_with_no_stored_naive_solution_is_not_searched_over(database, monkeypatch):
    """One landed before the role existed. The site's own answer would be
    judged by a search that cannot run."""
    cards = landed(database, monkeypatch)
    log = SolutionLog(database)
    kept = [one for one in log.solutions() if one.role is not SolutionRole.NAIVE]
    log.path.write_text("".join(one.model_dump_json() + "\n" for one in kept))

    _, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards)

    assert CallSite.INPUTS not in sites(outcomes)


def test_a_replayed_record_names_the_problem_it_answered(database, monkeypatch):
    """The item is the stored problem, which is what two configurations are
    compared over."""
    cards = landed(database, monkeypatch)

    _, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards)

    (stored,) = ProblemStore(database).all()
    assert {one.problem_id for one in outcomes} == {stored.id}


def test_a_pair_this_configuration_answered_is_skipped(database, monkeypatch):
    """The second run buys the same verdict at the same prompt hash, so it is
    not paid for."""
    cards = landed(database, monkeypatch)
    log = OutcomeLog(database)
    replayed(database, FakeWriter(generator=BUILDS), cards, log=log)

    second = FakeWriter(generator=BUILDS)
    result, outcomes = replayed(database, second, cards, log=log)

    assert second.calls == []
    assert result.asked == 0
    assert result.skipped == 3
    assert len(outcomes) == 3


def test_a_second_configuration_is_paid_for(database, monkeypatch):
    """A record answers for the configuration that wrote it and no other, or a
    cheaper model would be scored on what the first one read."""
    cards = landed(database, monkeypatch)
    log = OutcomeLog(database)
    replayed(database, FakeWriter(generator=BUILDS), cards, log=log)

    other = Bench(blind=Configuration(model="another", effort="medium", pin="one"))
    result, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards, log=log, bench=other)

    assert result.asked == 1
    assert result.skipped == 2
    assert [one.model for one in outcomes if one.site is CallSite.BLIND][-1] == "another"


def test_fresh_asks_again_where_a_record_answers(database, monkeypatch):
    """Measuring a reader against itself is what the skip would otherwise
    make unreachable."""
    cards = landed(database, monkeypatch)
    log = OutcomeLog(database)
    replayed(database, FakeWriter(generator=BUILDS), cards, log=log)

    result, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards, log=log, fresh=True)

    assert result.asked == 3
    assert len(outcomes) == 6


def test_a_replayed_reference_that_disagrees_is_recorded(database, monkeypatch):
    """The site's answer is settled against the cases the problem already
    carries, so a second reading of the statement is what is being scored."""
    cards = landed(
        database, monkeypatch, templates=[template("longest-valid-window", speedup=False)]
    )
    apart = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n", generator=BUILDS)

    _, outcomes = replayed(database, apart, cards)

    one = sites(outcomes)[CallSite.BLIND]
    assert one.gate is Gate.DISAGREED
    assert "disagree on 1 case(s)" in one.detail


def test_a_replay_writes_nothing_to_the_corpus(database, monkeypatch):
    """A case a round wins here is not appended, or the next configuration
    would be measured against a different problem."""
    cards = landed(database, monkeypatch)
    before = len(CaseLog(database).cases()), len(SolutionLog(database).solutions())

    replayed(database, FakeWriter(generator=BUILDS), cards)

    assert (len(CaseLog(database).cases()), len(SolutionLog(database).solutions())) == before


def test_a_retired_problem_is_not_replayed(database, monkeypatch):
    """A defective problem was never a fair test, and a later corpus will not
    hold it."""
    cards = landed(database, monkeypatch)
    store = ProblemStore(database)
    (one,) = store.all()
    store.put(
        one.model_copy(
            update={
                "status": ProblemStatus.RETIRED,
                "retired_reason": RetirementReason.DEFECTIVE,
            }
        )
    )

    result, outcomes = replayed(database, FakeWriter(generator=BUILDS), cards)

    assert result.asked == 0
    assert outcomes == []


def test_a_form_that_is_its_own_optimum_is_not_asked(database, monkeypatch):
    """Nothing separates the two solutions there, so the site has no question
    and the pair costs nothing rather than being skipped."""
    cards = landed(
        database, monkeypatch, templates=[template("longest-valid-window", speedup=False)]
    )

    result, outcomes = replayed(database, FakeWriter(), cards)

    assert CallSite.INPUTS not in sites(outcomes)
    assert CallSite.NAIVE not in sites(outcomes)
    assert result.asked == 1  # the reference alone


def test_the_discrimination_site_is_asked_where_a_mutant_survives(database, monkeypatch):
    """The survivors are in the prompt, so the prompt hash that decides the skip
    is known only after the local kill pass."""
    # the landing run's own round proposed a case that killed nothing, so the
    # stored set is the one written with the statement and a mutant is still
    # standing
    cards = landed(
        database,
        monkeypatch,
        FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES, separators=[[[0]]]),
        # no input generator is written for it, which holds a draft claiming a
        # speedup: nothing then demonstrates the claim
        templates=[template("longest-valid-window", speedup=False)],
    )

    _, outcomes = replayed(
        database,
        FakeWriter(canonical=BRANCHING, solution=AGREES, separators=[[[4], [3]]]),
        cards,
    )

    one = sites(outcomes)[CallSite.DISCRIMINATION]
    assert one.mutants > 0


def test_the_loop_is_replayed_against_the_set_as_it_stood(database):
    """A case a round won was not in the set the survivors were decided against.
    Counted, it would send another prompt hash, and the verdict the landing run
    recorded at the same configuration would be paid for twice."""
    log = OutcomeLog(database)
    (one,) = seeded(database, card())
    write_problems(
        FakeWriter(
            generator=BUILDS,
            canonical=BRANCHING,
            solution=AGREES,
            cases=DECIDES,
            separators=[[[4], [3]]],
        ),
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        outcomes=log,
    )
    assert {case.round for case in CaseLog(database).cases()} == {0, 1}

    second = FakeWriter(generator=BUILDS, canonical=BRANCHING, solution=AGREES)
    result, _ = replayed(database, second, [one], log=log)

    # skipped rather than unasked: shown the won case the loop kills every
    # mutant, and the site would go unasked for the wrong reason. The inputs
    # and naive sites are the unasked ones, since the form claims no speedup
    assert (result.skipped, result.unasked) == (2, 2)
    assert second.answered == 0


def test_the_sites_a_replay_asks_exclude_the_generator(tmp_path):
    """It writes a problem rather than answering one, so asking it again is
    `generate`."""
    assert CallSite.GENERATOR not in REPLAYED
    assert set(REPLAYED) == {
        CallSite.BLIND,
        CallSite.DISCRIMINATION,
        CallSite.INPUTS,
        CallSite.NAIVE,
    }
