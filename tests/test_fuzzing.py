from helpers import a_call

from algo_coach.generation.fuzzing import SEEDS, SIZES, build, fuzz, grid
from algo_coach.mutation import mutants
from algo_coach.schema import ExpectedSource

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
        call=a_call(),
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

    assert found.cases[0].call.id == "call-1"


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
