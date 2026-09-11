import pytest
from helpers import a_call

from algo_coach.generation.speedup import CEILING, MARGIN, Missing, search
from algo_coach.runner import weighs
from algo_coach.schema import ExpectedSource, MachineProvenance

# a naive solution whose cost grows with the square of the size, as a naive
# solution usually does. Two sleeps take 20ms and three take 45ms, and the cap
# sits between them, so a bound of two finishes. Which size the search settles
# on is the naive solution's answer rather than the search's, and no test
# asserts a number: a loaded machine moves it by one where the behaviour under
# test is the same
SLEEPS = "import time\n\n\ndef solve(n):\n    time.sleep(n * n / 200)\n    return n\n"
FAST = "def solve(n):\n    return n\n"
CAP_MS = 37
MEASURE_MS = 2000


def searched(canonical: str = FAST, naive: str = SLEEPS, reference: str = FAST, **overrides):
    """The naive solution is what the walk times; the reference is what settles
    the case at the size it stops on."""
    return search(
        overrides.pop("make", lambda size: [size]),
        canonical=canonical,
        naive=naive,
        reference=reference,
        provenance=MachineProvenance.of(a_call()),
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

    assert found.case.provenance.call_id == "call-1"


def test_the_separating_case_was_won_by_no_round():
    """The search runs after the loop, so the case was never in the set the
    survivors were decided against."""
    assert searched().case.round is None


def test_both_measurements_are_carried():
    """A later search reads these rather than running the whole set again."""
    found = searched()

    assert found.naive_ms >= CAP_MS
    assert found.canonical_ms < CAP_MS


def test_a_naive_solution_that_finishes_everywhere_separates_nothing():
    """A defect where the template claimed a speedup, and nothing at all where
    it did not."""
    found = searched(largest=2)

    assert not found.found
    assert found.missing is Missing.NAIVE_FINISHED


def test_the_largest_legal_size_is_tried_before_the_search_gives_up():
    """Doubling from one reaches two and then four, so a bound of three is
    reached by clamping alone. A naive solution that fits everywhere is what
    makes the sizes it was asked for readable."""
    asked: list[int] = []

    def make(size: int) -> list[int]:
        asked.append(size)
        return [size]

    searched(naive=FAST, largest=3, make=make)

    assert asked == [1, 2, 3]


def test_a_canonical_that_cannot_answer_at_that_size_separates_nothing():
    """The form gives no usable speedup at this cap, which is not a case."""
    found = searched(canonical=SLEEPS)

    assert found.missing is Missing.CANONICAL_FAILED


# one sleep of 8ms at any size: over a tenth of the cap, and inside the cap by
# more than a loaded machine delays one wakeup. A sleep per call of a count
# summed a delay per wakeup, and crossed the cap under the suite's own load
TENTH_SLOW = "import time\n\n\ndef solve(n):\n    time.sleep(0.008)\n    return n\n"


def test_a_canonical_over_a_tenth_of_the_cap_separates_nothing():
    """A case the canonical only just answers fails a correct submission a few
    percent slower, so the margin is what makes it a test of the form."""
    found = searched(canonical=TENTH_SLOW)

    assert found.missing is Missing.CANONICAL_TOO_SLOW
    assert found.canonical_ms * MARGIN > CAP_MS


def test_a_naive_solution_that_crashes_is_neither():
    """A recursion limit at size says nothing about how long the naive
    solution takes."""
    found = searched(naive="def solve(n):\n    raise ValueError(n)\n")

    assert found.missing is Missing.NAIVE_CRASHED


def test_a_naive_solution_beyond_the_measuring_cap_carries_no_time():
    """It exceeded the cap being separated, and by how much was never
    measured."""
    found = searched(naive="def solve(n):\n    while True:\n        pass\n", measure_ms=200)

    assert found.found
    assert found.size == 1
    assert found.naive_ms is None


def test_the_measuring_cap_sits_above_the_cap_being_separated():
    """Measured at the cap itself, every separating run is a timeout and no
    time is read from it."""
    with pytest.raises(ValueError, match="measuring cap"):
        searched(measure_ms=CAP_MS)


def test_the_search_starts_within_the_constraints():
    with pytest.raises(ValueError, match="smallest size"):
        searched(smallest=20, largest=16)


def test_an_input_over_the_ceiling_is_not_a_case():
    """A stored case is read whole on every verification, so what it may weigh
    is bounded rather than left to the separating size. The count step then
    finds nothing either, since a solution that returns a length has no time
    the cap can be divided by."""
    found = search(
        lambda size: [list(range(size))],
        canonical="def solve(xs):\n    return len(xs)\n",
        naive="def solve(xs):\n    return len(xs)\n",
        reference="def solve(xs):\n    return len(xs)\n",
        provenance=MachineProvenance.of(a_call()),
        cap_ms=CAP_MS,
        largest=10_000,
        measure_ms=MEASURE_MS,
        ceiling=64,
    )

    assert found.missing is Missing.COUNT_TOO_LARGE


def test_the_walk_tries_the_largest_storable_input_before_giving_up():
    """Doubling leaves a factor of two under the ceiling untried, and a
    quadratic naive solution separates in that gap. Three fits and four does
    not, and the naive solution exceeds the cap at three."""
    # the case weighs its answer beside its arguments
    ceiling = weighs([list(range(3))]) + weighs(3)
    listed = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) ** 2 / 200)\n"
    listed += "    return len(xs)\n"

    found = searched(
        make=lambda size: [list(range(size))],
        canonical="def solve(xs):\n    return len(xs)\n",
        naive=listed,
        reference="def solve(xs):\n    return len(xs)\n",
        ceiling=ceiling,
    )

    assert found.found
    assert found.size <= 3


def unstorable():
    """A search that reaches a separating size and cannot store the case: the
    arguments fit and the answer does not, which the case carries together."""
    big = "    return list(range(10000))\n"
    return searched(
        canonical="def solve(n):\n" + big,
        naive="import time\n\n\ndef solve(n):\n    time.sleep(n / 100)\n" + big,
        reference="def solve(n):\n" + big,
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
    assert found.naive_ms >= CAP_MS
    assert found.canonical_ms < CAP_MS


def test_a_naive_solution_that_finishes_is_told_from_an_input_that_does_not_fit():
    """One is a defect where a speedup was claimed, the other a problem whose
    separating input is out of reach."""
    assert searched(largest=2).missing is Missing.NAIVE_FINISHED


def test_the_case_carries_the_reference_s_answer_and_not_the_naive_solution_s():
    """Two solutions, two jobs: the naive one is timed and the reference is
    what says what the case returns."""
    found = searched(naive="import time\n\n\ndef solve(n):\n    time.sleep(n)\n    return -n\n")

    assert found.case.expected == found.size
    assert found.case.expected_from is ExpectedSource.REFERENCE


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


# one call is 3ms against a cap of 37, so the ceiling stops the size walk long
# before the naive solution is slow enough and only a count separates the two
SLOW_ONCE = "import time\n\n\ndef solve(xs):\n    time.sleep(0.003)\n    return len(xs)\n"
COUNTS = "def solve(xs):\n    return len(xs)\n"


def counted(**overrides):
    """A walk the ceiling ends with the naive solution under the cap, which is
    what a sublinear form leaves. A list of `size` zeros weighs three bytes an
    element, so forty stops the walk on an input a case can still carry."""
    return searched(
        canonical=overrides.pop("canonical", COUNTS),
        naive=overrides.pop("naive", SLOW_ONCE),
        reference=overrides.pop("reference", COUNTS),
        make=overrides.pop("make", lambda size: [[0] * size]),
        largest=overrides.pop("largest", 64),
        ceiling=overrides.pop("ceiling", 40),
        **overrides,
    )


def test_a_walk_the_ceiling_ended_separates_by_the_count():
    """A form whose one application is sublinear separates on no input the
    ceiling holds, and repeating the call reaches the cap on the one it does."""
    found = counted()

    assert found.found
    assert found.repeats > 1
    assert found.naive_ms > CAP_MS


def test_the_case_carries_the_count_the_search_settled_on():
    """The case separates under its own terms, so a verification that ran it
    once would pass the solution the search timed out."""
    found = counted()

    assert found.case.repeats == found.repeats


def test_a_count_no_ceiling_bounds_still_stops():
    """The cap divided by a time of nothing is unbounded, and a search that
    walked it would spend the run."""
    found = counted(naive=COUNTS)

    assert found.missing is Missing.COUNT_TOO_LARGE


def test_a_size_the_statement_bounds_is_not_repeated():
    """A walk that reached the statement's own bound is a defect in the run,
    which `corpus.md` names, rather than a size the ceiling hid."""
    found = counted(largest=2, ceiling=CEILING)

    assert found.missing is Missing.NAIVE_FINISHED
