from helpers import a_call

from algo_coach.generation.fuzzing import (
    SEEDS,
    SIZES,
    Candidate,
    build,
    fuzz,
    grid,
    shrink,
)
from algo_coach.mutation import kill, mutants, survivors
from algo_coach.runner import outputs
from algo_coach.schema import ExpectedSource, MachineProvenance

# a boundary decision, and a reference that agrees with it by another route
BOUNDED = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
# one argument per pair, so a size and a seed name the value the case carries
COUNTS = "def solve(size, seed):\n    return [size + seed]\n"

CAP_MS = 2_000


def fuzzed(inputs, *, canonical: str = BOUNDED, reference: str = AGREES):
    return fuzz(
        mutants(canonical),
        inputs,
        canonical=canonical,
        reference=reference,
        written=MachineProvenance.of(a_call()),
        cap_ms=CAP_MS,
        against_ms=CAP_MS,
    )


def test_the_grid_stays_inside_what_the_statement_allows():
    """A size above the bound builds an input the problem excludes, so no
    mutant it kills is evidence about the solution."""
    assert grid(2) == [[1, seed] for seed in SEEDS] + [[2, seed] for seed in SEEDS]
    assert grid(SIZES[-1] + 100) == [[size, seed] for size in SIZES for seed in SEEDS]


def test_a_seed_varies_the_input_at_one_size():
    """What the pass is for: one input per size would be five inputs, and a
    boundary is reached by the value rather than by the length."""
    assert build(COUNTS, [[1, 0], [1, 3]], cap_ms=CAP_MS) == [[1], [4]]


def test_an_input_that_kills_nothing_is_not_kept():
    """Every later verification would run it and it catches nothing. The three
    separate one mutant between them, and the first of them killed it."""
    found = fuzzed([[10], [11], [12]])

    assert [one.args for one in found.cases] == [[10]]
    assert found.built == 3


def test_the_first_input_that_kills_is_the_one_kept():
    """Two inputs killing one mutant are one case, and the smaller of them is
    the smaller case."""
    found = fuzzed([[3], [3], [3]])

    assert len(found.cases) == 1
    assert found.cases[0].args == [3]


def test_what_it_keeps_carries_the_reference_s_answer():
    """Settled as any other case: one the canonical produced would pass by
    construction, and the fuzz pass is where the canonical is the oracle."""
    found = fuzzed([[3]])

    (case,) = found.cases
    assert case.expected is False
    assert case.expected_from is ExpectedSource.REFERENCE
    # in the set the first round's survivors are decided against
    assert case.round == 0


def test_the_case_names_the_call_that_built_it():
    """The arguments were proposed by the input generator's code, not by the
    call that wrote the statement."""
    found = fuzzed([[3]])

    assert found.cases[0].written.call_id == "call-1"


def test_an_input_the_canonical_cannot_answer_is_dropped():
    """Nothing checks a built input against the constraints the statement
    gives, so a crash there says as much about the input as about the code."""
    found = fuzzed([["not a number"], [3]])

    assert found.dropped == 1
    assert [one.args for one in found.cases] == [[3]]


def test_two_solutions_disagreeing_on_a_kept_input_is_reported():
    """As a round's proposal is: the caller discards the problem, since the
    statement admits two readings."""
    found = fuzzed([[3]], reference="def solve(n):\n    return n > 2\n")

    assert found.disagreement is not None
    assert found.disagreement.args == [3]


def test_it_stops_once_nothing_stands():
    """The inputs after the last kill are runs nobody needs."""
    found = fuzzed([[1], [3], [4], [0]])

    assert found.standing == []
    assert [one.args for one in found.cases] == [[1], [3], [4]]


# a decision the length alone turns on, so a long input kills what a short one
# does and the shrink has somewhere to go
LONGEST = "def solve(xs):\n    return len(xs) > 2\n"


def caught(one: Candidate, canonical: str):
    """The mutants this input killed, which is what a shrink has to keep
    killing."""
    alive = mutants(canonical)
    left = [each.mutant for each in survivors(kill(alive, [one], cap_ms=CAP_MS))]
    return [each for each in alive if each not in left]


def shrunk(args, **overrides):
    canonical = overrides.pop("canonical", LONGEST)
    [expected] = outputs(canonical, [args], cap_ms=CAP_MS)
    one = Candidate(args=args, expected=expected)
    return shrink(
        one,
        caught(one, canonical),
        canonical=canonical,
        cap_ms=CAP_MS,
        against_ms=CAP_MS,
        **overrides,
    )


def test_a_killing_input_is_shrunk_to_what_the_kill_needs():
    """Every later verification runs the stored case, so the size is paid once
    to build and forever to run."""
    found = shrunk([list(range(12))])

    assert len(found.args[0]) < 12


def test_the_shrunk_input_carries_its_own_answer():
    """The canonical is run again on it: a case keeping the answer to the input
    it was shrunk from would fail the solution it was written from."""
    found = shrunk([list(range(12))])

    [answer] = outputs(LONGEST, [found.args], cap_ms=CAP_MS)
    assert found.expected == answer


def test_it_shrinks_no_further_than_the_kill_survives():
    """A mutant the shrunk input no longer catches is one the pass reported as
    killed and nothing kills."""
    original = Candidate(args=[list(range(12))], expected=True)

    found = shrunk([list(range(12))])

    assert not survivors(kill(caught(original, LONGEST), [found], cap_ms=CAP_MS))


def test_an_argument_that_is_not_a_list_is_left_alone():
    """A smaller number is a different question the statement answers, where a
    shorter list is the same one asked of less."""
    found = shrunk([list(range(8)), 5], canonical="def solve(xs, k):\n    return len(xs) > k\n")

    assert found.args[1] == 5


def test_the_budget_bounds_what_one_shrink_costs():
    """Each candidate is a run of the canonical and one per mutant, so an input
    nothing shrinks would otherwise spend the pass's whole runtime."""
    found = shrunk([list(range(12))], tries=0)

    assert found.args == [list(range(12))]


# agrees with `LONGEST` by another route, so a kept input settles rather than
# discarding the problem
LONGEST_BLIND = "def solve(xs):\n    return not len(xs) <= 2\n"


def test_what_the_pass_stores_is_the_shrunk_input():
    """The case a problem carries is run by every later verification, so the
    pass stores what the kill needs rather than what the size built."""
    found = fuzzed([[list(range(12))]], canonical=LONGEST, reference=LONGEST_BLIND)

    (case,) = found.cases
    assert len(case.args[0]) < 12


def test_an_input_over_the_ceiling_is_kept_once_it_fits():
    """The ceiling rejected a killing input outright, where the shrink is what
    makes it storable."""
    found = fuzz(
        mutants(LONGEST),
        [[list(range(12))]],
        canonical=LONGEST,
        reference=LONGEST_BLIND,
        written=MachineProvenance.of(a_call()),
        cap_ms=CAP_MS,
        against_ms=CAP_MS,
        ceiling=40,
    )

    assert len(found.cases) == 1


def test_an_input_the_shrink_cannot_bring_under_the_ceiling_is_not_kept():
    """A case no store can carry, and the mutants it caught stay standing since
    nothing kills them."""
    found = fuzz(
        mutants(LONGEST),
        [[list(range(12))]],
        canonical=LONGEST,
        reference=LONGEST_BLIND,
        written=MachineProvenance.of(a_call()),
        cap_ms=CAP_MS,
        against_ms=CAP_MS,
        ceiling=1,
    )

    assert found.cases == []
    assert len(found.standing) == len(mutants(LONGEST))
