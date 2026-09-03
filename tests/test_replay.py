from generating import FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog, Configuration
from algo_coach.cases import CaseLog
from algo_coach.generation import Bench, Corpus, replay, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import CallSite, Discard, ProblemStatus, RetirementReason
from algo_coach.solutions import SolutionLog

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]


def landed(tmp_path, model: FakeWriter | None = None, **overrides):
    """One stored problem, written by a run that recorded no outcome of its
    own, so a replay's store starts empty."""
    (one,) = seeded(tmp_path, card(**overrides))
    write_problems(
        model or FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
    )
    return [one]


def replayed(tmp_path, model: FakeWriter, cards, *, log=None, **kw):
    log = log or OutcomeLog(tmp_path)
    result = replay(model, CallLog(tmp_path), Corpus.at(tmp_path), log, cards, **kw)
    return result, log.outcomes()


def sites(outcomes) -> dict[CallSite, object]:
    return {one.site: one for one in outcomes}


def test_a_replay_asks_the_answering_sites_about_a_stored_problem(tmp_path):
    """Generation writes a new problem every time, so a configuration is
    compared with another only over a statement that already exists."""
    cards = landed(tmp_path)

    result, outcomes = replayed(tmp_path, FakeWriter(generator=BUILDS), cards)

    assert set(sites(outcomes)) == {CallSite.BLIND, CallSite.INPUTS}
    assert result.asked == 2


def test_a_replayed_record_names_the_problem_it_answered(tmp_path):
    """The item is the stored problem, which is what two configurations are
    compared over."""
    cards = landed(tmp_path)

    _, outcomes = replayed(tmp_path, FakeWriter(generator=BUILDS), cards)

    (stored,) = ProblemStore(tmp_path).all()
    assert {one.problem_id for one in outcomes} == {stored.id}


def test_a_pair_this_configuration_answered_is_skipped(tmp_path):
    """The second run buys the same verdict at the same digest, so it is not
    paid for."""
    cards = landed(tmp_path)
    log = OutcomeLog(tmp_path)
    replayed(tmp_path, FakeWriter(generator=BUILDS), cards, log=log)

    second = FakeWriter(generator=BUILDS)
    result, outcomes = replayed(tmp_path, second, cards, log=log)

    assert second.calls == []
    assert result.asked == 0
    assert result.skipped == 2
    assert len(outcomes) == 2


def test_a_second_configuration_is_paid_for(tmp_path):
    """A record answers for the configuration that wrote it and no other, or a
    cheaper model would be scored on what the first one read."""
    cards = landed(tmp_path)
    log = OutcomeLog(tmp_path)
    replayed(tmp_path, FakeWriter(generator=BUILDS), cards, log=log)

    other = Bench(blind=Configuration(model="another", effort="medium", pin="one"))
    result, outcomes = replayed(tmp_path, FakeWriter(generator=BUILDS), cards, log=log, bench=other)

    assert result.asked == 1
    assert result.skipped == 1
    assert [one.model for one in outcomes if one.site is CallSite.BLIND][-1] == "another"


def test_fresh_asks_again_where_a_record_answers(tmp_path):
    """Measuring a reader against itself is what the skip would otherwise
    make unreachable."""
    cards = landed(tmp_path)
    log = OutcomeLog(tmp_path)
    replayed(tmp_path, FakeWriter(generator=BUILDS), cards, log=log)

    result, outcomes = replayed(tmp_path, FakeWriter(generator=BUILDS), cards, log=log, fresh=True)

    assert result.asked == 2
    assert len(outcomes) == 4


def test_a_replayed_reference_that_disagrees_is_recorded(tmp_path):
    """The site's answer is settled against the cases the problem already
    carries, so a second reading of the statement is what is being scored."""
    cards = landed(tmp_path)
    apart = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n", generator=BUILDS)

    _, outcomes = replayed(tmp_path, apart, cards)

    one = sites(outcomes)[CallSite.BLIND]
    assert one.gate is Discard.DISAGREED
    assert "disagrees on 1 case(s)" in one.detail


def test_a_replay_writes_nothing_to_the_corpus(tmp_path):
    """A case a round wins here is not appended, or the next configuration
    would be measured against a different problem."""
    cards = landed(tmp_path)
    before = len(CaseLog(tmp_path).cases()), len(SolutionLog(tmp_path).solutions())

    replayed(tmp_path, FakeWriter(generator=BUILDS), cards)

    assert (len(CaseLog(tmp_path).cases()), len(SolutionLog(tmp_path).solutions())) == before


def test_a_retired_problem_is_not_replayed(tmp_path):
    """A defective problem was never a fair test, and a telegraphed one is not
    what a later corpus will hold."""
    cards = landed(tmp_path)
    store = ProblemStore(tmp_path)
    (one,) = store.all()
    store.put(
        one.model_copy(
            update={
                "status": ProblemStatus.RETIRED,
                "retired_reason": RetirementReason.TELEGRAPHED,
            }
        )
    )

    result, outcomes = replayed(tmp_path, FakeWriter(generator=BUILDS), cards)

    assert result.asked == 0
    assert outcomes == []


def test_a_form_that_is_its_own_optimum_is_not_asked(tmp_path):
    """Nothing separates the two solutions there, so the site has no question
    and the pair costs nothing rather than being skipped."""
    cards = landed(tmp_path, templates=[template("longest-valid-window", speedup=False)])

    result, outcomes = replayed(tmp_path, FakeWriter(), cards)

    assert CallSite.INPUTS not in sites(outcomes)
    assert result.asked == 1  # the reference alone


def test_the_discrimination_site_is_asked_where_a_mutant_survives(tmp_path):
    """The survivors are in the prompt, so the digest that decides the skip is
    known only after the local kill pass."""
    # the landing run's own round answered nothing, so the stored set is the
    # one written with the statement and a mutant is still standing
    cards = landed(tmp_path, FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES))

    _, outcomes = replayed(
        tmp_path,
        FakeWriter(canonical=BRANCHING, solution=AGREES, separators=[[[4], [3]]]),
        cards,
    )

    one = sites(outcomes)[CallSite.DISCRIMINATION]
    assert one.mutants > 0


def test_the_loop_is_replayed_against_the_set_as_it_stood(tmp_path):
    """A case a round won was not in the set the survivors were decided
    against. Counted, it would send another digest, and the verdict the landing
    run recorded at the same configuration would be paid for twice."""
    log = OutcomeLog(tmp_path)
    (one,) = seeded(tmp_path, card())
    write_problems(
        FakeWriter(
            generator=BUILDS,
            canonical=BRANCHING,
            solution=AGREES,
            cases=DECIDES,
            separators=[[[4], [3]]],
        ),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        outcomes=log,
    )
    assert {case.round for case in CaseLog(tmp_path).cases()} == {0, 1}

    second = FakeWriter(generator=BUILDS, canonical=BRANCHING, solution=AGREES)
    result, _ = replayed(tmp_path, second, [one], log=log)

    # skipped rather than unasked: shown the won case the loop kills every
    # mutant, and the site would go unasked for the wrong reason
    assert (result.skipped, result.unasked) == (3, 0)
    assert second.answered == 0


def test_the_sites_a_replay_asks_exclude_the_generator(tmp_path):
    """It writes a problem rather than answering one, so asking it again is
    `generate`."""
    from algo_coach.generation import REPLAYED

    assert CallSite.GENERATOR not in REPLAYED
    assert set(REPLAYED) == {CallSite.BLIND, CallSite.DISCRIMINATION, CallSite.INPUTS}
