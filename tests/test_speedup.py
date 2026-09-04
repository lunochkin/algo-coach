import pytest
from helpers import a_call

from algo_coach.generation.speedup import CEILING, Missing, search
from algo_coach.schema import ExpectedSource, MachineProvenance

# a reference whose cost grows with the square of the size, as a naive solution
# usually does. Two sleeps take 20ms and three take 45ms, and the cap sits
# between them, so a bound of two finishes. Which size the search settles on is
# the clock's answer rather than the search's, and no test asserts a number: a
# loaded machine moves it by one where the behaviour under test is the same
SLEEPS = "import time\n\n\ndef solve(n):\n    time.sleep(n * n / 200)\n    return n\n"
FAST = "def solve(n):\n    return n\n"
CAP_MS = 37
MEASURE_MS = 2000


def searched(canonical: str = FAST, reference: str = SLEEPS, **overrides):
    return search(
        overrides.pop("make", lambda size: [size]),
        canonical=canonical,
        reference=reference,
        written=MachineProvenance.of(a_call()),
        cap_ms=overrides.pop("cap_ms", CAP_MS),
        largest=overrides.pop("largest", 16),
        measure_ms=overrides.pop("measure_ms", MEASURE_MS),
        ceiling=overrides.pop("ceiling", CEILING),
        **overrides,
    )


def test_the_size_it_settles_on_is_the_smallest_that_exceeds():
    """The halving is what makes it the smallest: the size below the one it
    returns was measured, and it fitted."""
    asked: list[int] = []

    def make(size: int) -> list[int]:
        asked.append(size)
        return [size]

    found = searched(make=make)

    assert found.found
    assert found.size - 1 in asked


def test_the_case_carries_the_arguments_at_that_size():
    """A size names no input on its own, so what is stored is what the
    generator built there."""
    found = searched()

    assert found.args == [found.size]


def test_the_case_names_the_call_that_wrote_the_input_generator():
    """The arguments are what that call's code built, so the search's own site
    is what the stored case compares under."""
    found = searched()

    assert found.case.written.call_id == "call-1"


def test_the_separating_case_was_won_by_no_round():
    """The search runs after the loop, so the case was never in the set the
    survivors were decided against."""
    assert searched().case.round is None


def test_both_measurements_are_carried():
    """A later search reads these rather than running the whole set again."""
    found = searched()

    assert found.reference_ms >= CAP_MS
    assert found.canonical_ms < CAP_MS


def test_a_reference_that_finishes_everywhere_separates_nothing():
    """A defect where the template claimed a speedup, and nothing at all where
    it did not."""
    found = searched(largest=2)

    assert not found.found
    assert found.missing is Missing.REFERENCE_FINISHED


def test_the_largest_legal_size_is_tried_before_the_search_gives_up():
    """Doubling from one reaches two and then four, so a bound of three is
    reached by clamping alone. A reference that fits everywhere is what makes
    the sizes it was asked for readable."""
    asked: list[int] = []

    def make(size: int) -> list[int]:
        asked.append(size)
        return [size]

    searched(reference=FAST, largest=3, make=make)

    assert asked == [1, 2, 3]


def test_a_canonical_that_cannot_answer_at_that_size_separates_nothing():
    """The form gives no usable speedup at this cap, which is not a case."""
    found = searched(canonical=SLEEPS)

    assert found.missing is Missing.CANONICAL_FAILED


def test_a_reference_that_crashes_is_neither():
    """A recursion limit at size says nothing about how long the naive
    solution takes."""
    found = searched(reference="def solve(n):\n    raise ValueError(n)\n")

    assert found.missing is Missing.REFERENCE_CRASHED


def test_a_reference_beyond_the_measuring_cap_carries_no_time():
    """It exceeded the cap being separated, and by how much was never
    measured."""
    found = searched(reference="def solve(n):\n    while True:\n        pass\n", measure_ms=200)

    assert found.found
    assert found.size == 1
    assert found.reference_ms is None


def test_the_measuring_cap_sits_above_the_cap_being_separated():
    """Measured at the cap itself, every separating run is a timeout and no
    time is read from it."""
    with pytest.raises(ValueError):
        searched(measure_ms=CAP_MS)


def test_the_search_starts_within_the_constraints():
    with pytest.raises(ValueError):
        searched(smallest=20, largest=16)


def test_an_input_over_the_ceiling_is_not_a_case():
    """A stored case is read whole on every verification, so what it may weigh
    is bounded rather than left to the separating size."""
    found = search(
        lambda size: [list(range(size))],
        canonical="def solve(xs):\n    return len(xs)\n",
        reference="def solve(xs):\n    return len(xs)\n",
        written=MachineProvenance.of(a_call()),
        cap_ms=CAP_MS,
        largest=10_000,
        measure_ms=MEASURE_MS,
        ceiling=64,
    )

    assert found.missing is Missing.INPUT_TOO_LARGE


def unstorable():
    """A search that reaches a separating size and cannot store the case: the
    arguments fit and the answer does not, which the case carries together."""
    big = "    return list(range(10000))\n"
    return searched(
        canonical="def solve(n):\n" + big,
        reference="import time\n\n\ndef solve(n):\n    time.sleep(n / 100)\n" + big,
        ceiling=200,
    )


def test_a_returned_value_over_the_ceiling_is_not_a_case():
    assert unstorable().missing is Missing.CASE_TOO_LARGE


def test_a_case_over_the_ceiling_is_told_from_a_walk_that_never_reached_one():
    """One proves the speedup and loses the case, the other looked nowhere. A
    run reading them as one answer cannot tell a defect from an unknown."""
    assert unstorable().missing is not Missing.INPUT_TOO_LARGE


def test_a_separation_it_proved_carries_the_size_and_both_times():
    """The speedup holds at that size, and the measurements are what say so.
    Without them the run reports nothing it paid to establish."""
    found = unstorable()

    assert found.size is not None
    assert found.reference_ms >= CAP_MS
    assert found.canonical_ms < CAP_MS


def test_a_reference_that_finishes_is_told_from_an_input_that_does_not_fit():
    """One is a defect where a speedup was claimed, the other a problem whose
    separating input is out of reach."""
    assert searched(largest=2).missing is Missing.REFERENCE_FINISHED


def test_the_expected_value_is_the_reference_s_where_it_computed_one():
    """The settle rule the first case set uses. A case the canonical produced
    passes by construction, and this one is a test of it."""
    found = searched()

    assert found.case.expected == found.size
    assert found.case.expected_from is ExpectedSource.REFERENCE


def test_the_expected_value_is_the_canonical_s_beyond_the_reference_s_reach():
    """Nothing else can compute it, and the case is then evidence about the
    cap rather than about the verdict."""
    found = searched(reference="def solve(n):\n    while True:\n        pass\n", measure_ms=200)

    assert found.case.expected_from is ExpectedSource.CANONICAL


def test_two_solutions_disagreeing_at_that_size_is_not_a_case():
    """A canonical correct on the small cases and wrong at scale is what the
    separating input catches."""
    found = searched(canonical="def solve(n):\n    return n + 1\n")

    assert found.missing is Missing.DISAGREED
    assert found.disagreement.canonical == found.disagreement.reference + 1
