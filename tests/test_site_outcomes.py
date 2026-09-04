from generating import FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog, Configuration
from algo_coach.generation import BENCH, Bench, Corpus, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import CallSite, Discard

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# four mutation sites, where `len(xs)` has none: what makes the loop ask
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]
# one argument per pair, so the grid reaches the boundary `BRANCHING` turns on
COUNTS = "def solve(size, seed):\n    return [size + seed]\n"


def run(tmp_path, model: FakeWriter, *, count: int = 1, bench: Bench = BENCH, **overrides):
    (one,) = seeded(tmp_path, card(**overrides))
    log = OutcomeLog(tmp_path)
    result = write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        count=count,
        bench=bench,
        outcomes=log,
    )
    return one, result, log.outcomes()


def sites(outcomes) -> dict[CallSite, object]:
    return {one.site: one for one in outcomes}


def test_every_site_that_answered_leaves_a_record(tmp_path):
    """A run prints its stages and the process then ends, so what a site was
    asked and what came of it is readable only from a record."""
    _, result, outcomes = run(tmp_path, FakeWriter(generator=BUILDS))

    assert len(result.drafted) == 1
    assert set(sites(outcomes)) == {CallSite.GENERATOR, CallSite.BLIND, CallSite.INPUTS}


def test_the_four_sites_of_one_attempt_share_a_writing_id(tmp_path):
    """Minted per attempt rather than taken from the problem: it is what groups
    the sites of a draft that never landed."""
    _, _, outcomes = run(tmp_path, FakeWriter(generator=BUILDS))

    assert len({one.writing_id for one in outcomes}) == 1


def test_a_landed_problem_is_named_by_its_records(tmp_path):
    """The eval reads a site's answers back per problem, and the id exists only
    once the problem lands."""
    _, _, outcomes = run(tmp_path, FakeWriter(generator=BUILDS))

    (stored,) = ProblemStore(tmp_path).all()
    assert {one.problem_id for one in outcomes} == {stored.id}


def test_a_discarded_draft_still_leaves_what_its_sites_left(tmp_path):
    """The draft is the attempt with nothing else to point at: unrecorded, what
    the run paid for is lost when it ends."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, result, outcomes = run(tmp_path, model)

    assert result.drafted == []
    assert set(sites(outcomes)) == {CallSite.GENERATOR, CallSite.BLIND}
    assert {one.problem_id for one in outcomes} == {None}


def test_a_disagreement_is_the_blind_sites_gate(tmp_path):
    """A gate is filed under the site whose answer made it decidable. Nothing
    disagrees until there is a second reading of the statement."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, _, outcomes = run(tmp_path, model)

    at = sites(outcomes)
    assert at[CallSite.BLIND].gate is Discard.DISAGREED
    assert at[CallSite.GENERATOR].gate is None


def test_a_reference_that_computed_nothing_is_the_blind_sites_gate(tmp_path):
    """Its whole purpose is computing the expected outputs, so a reference that
    answered no case failed at what it was asked for."""
    model = FakeWriter(solution="def solve(xs):\n    raise ValueError\n")

    _, _, outcomes = run(tmp_path, model)

    assert sites(outcomes)[CallSite.BLIND].gate is Discard.UNTESTED


def test_a_canonical_contradicting_its_own_cases_is_the_generators_gate(tmp_path):
    """One call wrote both, so a disagreement between them is that call's
    mistake and no reading of the statement is involved."""
    model = FakeWriter(cases=[{"args": "[[1, 2, 3]]", "expected": "99"}])

    _, _, outcomes = run(tmp_path, model)

    at = sites(outcomes)
    assert at[CallSite.GENERATOR].gate is Discard.MISDECLARED
    assert "contradicts 1 case(s)" in at[CallSite.GENERATOR].detail


def test_each_record_carries_the_configuration_of_its_own_call(tmp_path):
    """Four models in one run stay readable because a record copies its own
    call's configuration rather than the run's."""
    bench = Bench(
        generator=Configuration(model="a-generator", effort="high", pin="one"),
        blind=Configuration(model="a-reference", effort="low", pin="two", temperature=0.0),
    )

    _, _, outcomes = run(tmp_path, FakeWriter(), bench=bench)

    at = sites(outcomes)
    assert at[CallSite.GENERATOR].model == "a-generator"
    assert at[CallSite.BLIND].model == "a-reference"
    assert at[CallSite.GENERATOR].prompt_hash != at[CallSite.BLIND].prompt_hash


def test_a_site_that_made_no_call_writes_nothing(tmp_path):
    """The set written with the statement killed every mutant, so no round was
    asked and the site paid for no configuration an eval could compare."""
    _, _, outcomes = run(tmp_path, FakeWriter(generator=BUILDS))

    assert CallSite.DISCRIMINATION not in sites(outcomes)


def test_a_form_that_is_its_own_optimum_records_the_builder_it_paid_for(tmp_path):
    """The input generator is written for every problem, so the site answered.
    Nothing was searched for, and the record carries neither a size nor a
    reason there was none."""
    _, _, outcomes = run(
        tmp_path,
        FakeWriter(generator=BUILDS),
        templates=[template("longest-valid-window", speedup=False)],
    )

    one = sites(outcomes)[CallSite.INPUTS]
    assert one.separating is None
    assert one.unseparated is None


def test_a_builder_call_that_failed_leaves_no_record(tmp_path):
    """Provenance is all or none, and a call that answered nothing carries
    none. The problem lands: the site says nothing about the statement."""
    _, result, outcomes = run(tmp_path, FakeWriter())

    assert len(result.drafted) == 1
    assert CallSite.INPUTS not in sites(outcomes)


def test_the_discrimination_record_carries_what_the_loop_left(tmp_path):
    """A round is what the site is scored on: the cases it won and the mutants
    they caught, one entry per round."""
    model = FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES, separators=[[[4], [3]]])

    _, _, outcomes = run(tmp_path, model)

    one = sites(outcomes)[CallSite.DISCRIMINATION]
    assert one.won > 0
    assert one.killed == sum(one.rounds)
    assert one.rounds[0] > 0


def test_the_record_says_what_a_round_proposed_and_what_landed(tmp_path):
    """A proposal that killed nothing is not stored, and the difference is what
    the call was paid for and got nothing from."""
    model = FakeWriter(
        canonical=BRANCHING, solution=AGREES, cases=DECIDES, separators=[[[100], [4], [3]]]
    )

    _, _, outcomes = run(tmp_path, model)

    one = sites(outcomes)[CallSite.DISCRIMINATION]
    assert one.offered == 3
    assert one.won == 2


def test_the_canonical_s_mutants_are_the_generator_s_own_count(tmp_path):
    """It wrote the solution the set is enumerated from, and its record is the
    one every attempt leaves."""
    model = FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES, separators=[[[4], [3]]])

    _, _, outcomes = run(tmp_path, model)

    assert sites(outcomes)[CallSite.GENERATOR].mutants > 0


def test_each_source_is_filed_under_the_site_whose_output_killed(tmp_path):
    """Whether a round earns its call is what the split answers, so the three
    sum to the mutants the canonical yielded."""
    model = FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES, separators=[[[4], [3]]])

    _, _, outcomes = run(tmp_path, model)

    at = sites(outcomes)
    killed = at[CallSite.GENERATOR].killed + at[CallSite.DISCRIMINATION].killed
    assert killed + at[CallSite.DISCRIMINATION].survived == at[CallSite.GENERATOR].mutants


def test_a_pass_that_needed_no_round_still_records_what_killed(tmp_path):
    """The attempt a round was never paid for is the one the measurement wants,
    and no discrimination record exists to carry it."""
    model = FakeWriter(canonical=BRANCHING, solution=AGREES, cases=DECIDES, generator=COUNTS)

    _, _, outcomes = run(tmp_path, model)

    at = sites(outcomes)
    assert CallSite.DISCRIMINATION not in at
    assert at[CallSite.INPUTS].killed > 0
    assert (
        at[CallSite.GENERATOR].killed + at[CallSite.INPUTS].killed == at[CallSite.GENERATOR].mutants
    )


def test_a_fuzz_disagreement_is_the_inputs_site_s_gate(tmp_path):
    """Nothing was decidable before the site's code built the input the two
    solutions answered differently, and the discrimination site was never
    asked."""
    model = FakeWriter(
        canonical=BRANCHING,
        solution="def solve(n):\n    return n > 2\n",
        cases=DECIDES,
        generator=COUNTS,
    )

    _, result, outcomes = run(tmp_path, model)

    assert [one.discard for one in result.discarded] == ["disagreed"]
    assert sites(outcomes)[CallSite.INPUTS].gate is Discard.DISAGREED
    assert CallSite.DISCRIMINATION not in sites(outcomes)


def test_the_sites_are_the_ones_the_bench_names(tmp_path):
    """One list, or a configuration would be set for a site no record can name."""
    assert set(Bench.model_fields) == {one.value for one in CallSite}


SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"


def test_the_inputs_record_carries_the_size_the_search_found(tmp_path, monkeypatch):
    """What the site is scored on: the code it wrote is what the search ran to
    reach a size."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    model = FakeWriter(solution=SLOW, generator=BUILDS)

    _, _, outcomes = run(tmp_path, model)

    one = sites(outcomes)[CallSite.INPUTS]
    assert one.separating == 2
    assert one.unseparated is None


def test_a_search_that_separated_nothing_says_why(tmp_path):
    """A missing separation is a defect only where a speedup was claimed, and
    the reason is what tells the two apart."""
    _, _, outcomes = run(tmp_path, FakeWriter(generator=BUILDS))

    one = sites(outcomes)[CallSite.INPUTS]
    assert one.separating is None
    assert one.unseparated == "reference_finished"
