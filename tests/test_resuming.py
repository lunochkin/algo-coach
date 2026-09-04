from generating import CANONICAL, FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog, Configuration
from algo_coach.drafts import DraftStore
from algo_coach.generation import BENCH, Bench, Corpus, moved_at, write_problems
from algo_coach.schema import Draft, Template, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# four mutation sites, so a survivor reaches a round and the loop pays a call
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]
OTHER = Configuration(model="another-model", effort="medium", pin="a-provider/bf16")


# the form these drafts were written under, and the same one claiming the
# speedup that makes the search run
OPTIMUM = Template(id="t1", **template("longest-valid-window"))
CLAIMS = Template(id="t1", **template("longest-valid-window", speedup=True))


def drafted(tmp_path) -> Draft:
    """A draft every answering site left a configuration on."""
    (one,) = seeded(tmp_path, card())
    model = FakeWriter(
        canonical=BRANCHING,
        solution=AGREES,
        cases=DECIDES,
        generator=BUILDS,
        separators=[[[4], [3]]],
    )
    result = write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=DraftStore(tmp_path),
    )
    (stored,) = result.drafted
    return stored


def test_an_unchanged_bench_moves_nothing(tmp_path):
    """The run wrote this draft at the bench's own configurations, and every
    digest is a function of the statement it already holds."""
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH) is None


def test_a_moved_blind_configuration_starts_at_the_reference(tmp_path):
    """The reference is written from the statement alone, so a second model
    reading it is a second reading rather than the stored one."""
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"blind": OTHER})) is (
        WritingState.REFERENCED
    )


def test_a_moved_inputs_configuration_starts_at_the_builder(tmp_path):
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"inputs": OTHER})) is (
        WritingState.BUILT
    )


def test_a_moved_discrimination_configuration_starts_at_the_loop(tmp_path):
    """Its digest carries the survivors, which only the local kill pass names,
    so the configuration is what answers here."""
    assert moved_at(
        drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"discrimination": OTHER})
    ) is (WritingState.HARDENED)


def test_the_earliest_moved_step_is_the_one_returned(tmp_path):
    """A resume goes forward only: a step's prompt is a function of the outputs
    before it, so the first moved step invalidates what follows."""
    bench = BENCH.model_copy(update={"blind": OTHER, "discrimination": OTHER})

    assert moved_at(drafted(tmp_path), OPTIMUM, bench) is WritingState.REFERENCED


def test_a_moved_generator_invalidates_no_draft(tmp_path):
    """The draft is that step's output, and a new prompt writes a different
    problem rather than the same one again."""
    assert (
        moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"generator": OTHER})) is None
    )


def test_a_stale_digest_starts_at_its_own_step(tmp_path):
    """An edited prompt moves the digest without moving the configuration, and
    a resume that read only the model would re-run nothing."""
    stored = drafted(tmp_path)
    stale = stored.blind.model_copy(update={"prompt_hash": "ffffffffffff"})

    assert moved_at(stored.model_copy(update={"blind": stale}), OPTIMUM, BENCH) is (
        WritingState.REFERENCED
    )


def test_a_step_the_draft_never_took_is_not_moved():
    """What to do about a step that never ran is the draft's state, not the
    bench's."""
    stopped = Draft(
        id="w1",
        state=WritingState.CHECKED,
        title="Widest fair stretch",
        statement="Given a list of readings, return ...",
        canonical=CANONICAL,
        declared=[{"args": [[1, 2, 3]], "expected": 3}],
        difficulty="medium",
    )

    assert (
        moved_at(stopped, OPTIMUM, Bench(blind=OTHER, inputs=OTHER, discrimination=OTHER)) is None
    )


def held(tmp_path) -> Draft:
    """A draft the search held: its template claims a speedup and the reference
    finished at every size the builder wrote."""
    (one,) = seeded(tmp_path, card(templates=[template("longest-valid-window", speedup=True)]))
    result = write_problems(
        FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=DraftStore(tmp_path),
    )
    (one,) = result.held
    return one.draft


def test_a_claim_that_still_stands_leaves_the_draft_at_the_search(tmp_path):
    """Nothing separated the two solutions, and the claim is what says a case
    has to."""
    assert moved_at(held(tmp_path), CLAIMS, BENCH) is None


def test_a_corrected_speedup_resumes_the_draft_the_search_held(tmp_path):
    """A flag edit moves neither a configuration nor a digest, so a resume
    reading only those would leave the draft where the search stopped it."""
    assert moved_at(held(tmp_path), OPTIMUM, BENCH) is WritingState.HARDENED


def test_a_moved_configuration_is_returned_over_a_corrected_flag(tmp_path):
    """A resume goes forward only, and the reference is written before the
    search."""
    bench = BENCH.model_copy(update={"blind": OTHER})

    assert moved_at(held(tmp_path), OPTIMUM, bench) is WritingState.REFERENCED
