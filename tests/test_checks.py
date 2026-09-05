import json

from helpers import a_call

from algo_coach.generation import Discard, agree, check, checks, stopped
from algo_coach.schema import CaseOutcome, DraftCase, ExpectedSource, MachineProvenance

DOUBLE = "def solve(x):\n    return x * 2\n"
# the same function reached another way, which is what a blind reference is
TWICE = "def solve(x):\n    return x + x\n"
CAP_MS = 1000


def cases(*pairs) -> list[DraftCase]:
    """Cases as the generation call wrote them: the arguments, and the value
    it declared `solve` returns. Both arrive as JSON text."""
    return [DraftCase(args=json.dumps(list(args)), expected=json.dumps(one)) for args, one in pairs]


def checked(*pairs, canonical: str = DOUBLE, reference: str = TWICE, cap_ms: int = CAP_MS):
    """The two steps as a run takes them: the canonical alone, and only where
    it survived, the reference against what it returned."""
    written = cases(*pairs)
    ran = check(written, canonical=canonical, cap_ms=cap_ms)
    if not ran.survived:
        return stopped(ran)
    return agree(
        ran, written, reference=reference, written=MachineProvenance.of(a_call()), cap_ms=cap_ms
    )


def test_a_problem_both_solutions_answer_the_same_way_survives():
    """The prose has one reading, and the canonical returns what its own call
    declared."""
    result = checked(([2], 4), ([5], 10))

    assert result.survived
    assert result.outcome is CaseOutcome.PASSED
    assert [one.args for one in result.cases] == [[2], [5]]


def test_the_set_written_with_the_statement_was_won_by_no_round():
    """Zero rather than absent: it is the set the mutation loop is first run
    against, and a replay rebuilds it from exactly these."""
    assert {one.round for one in checked(([2], 4), ([5], 10)).cases} == {0}


def test_a_landing_case_carries_the_reference_s_answer():
    """A case the canonical produced passes by construction, so the stored
    value is the one the independent solution computed."""
    result = checked(([2], 4))

    assert [one.expected for one in result.cases] == [4]


def test_a_canonical_yielding_no_value_discards_the_problem():
    """Nothing establishes what the case returns, so there is no problem to
    keep."""
    result = checked(([2], 4), canonical="def solve(x):\n    raise ValueError(x)\n")

    assert not result.survived
    assert result.discard is Discard.NO_VALUE
    assert result.outcome is CaseOutcome.CRASHED
    assert result.cases == []


def test_a_canonical_contradicting_its_own_cases_is_counted_not_discarded():
    """One call wrote the code and the declaration, so they share a reading.
    What the case stores is the reference's answer either way."""
    result = checked(([2], 4), ([5], 11))

    assert result.survived
    # the fold says how the run went: a declaration it contradicts is counted,
    # and only the reference can call an answer wrong
    assert result.outcome is CaseOutcome.PASSED
    assert [one.returned for one in result.misdeclarations] == [10]
    assert [one.expected for one in result.cases] == [4, 10]


def test_the_reference_is_never_run_where_the_canonical_yielded_no_value(monkeypatch):
    """Nothing establishes what the case returns, so there is nothing for a
    second solution to be settled against."""

    def unreachable(*args, **kwargs):
        raise AssertionError("the reference was run")

    monkeypatch.setattr(checks, "outputs", unreachable)
    canonical = "def other():\n    return 1\n"

    assert checked(([2], 4), canonical=canonical).discard is Discard.NO_VALUE


def test_two_solutions_that_disagree_discard_the_problem():
    """The prose admits two readings, which is the statement's fault rather
    than either solution's."""
    result = checked(([2], 4), ([5], 10), reference="def solve(x):\n    return x * 3\n")

    assert result.discard is Discard.DISAGREED
    assert [one.args for one in result.disagreements] == [[2], [5]]
    assert result.cases == []


def test_a_canonical_that_passed_its_own_cases_can_still_be_discarded():
    """The gates are ordered, and the run's outcome is a fact about the
    canonical rather than about whether the problem was kept."""
    result = checked(([2], 4), reference="def solve(x):\n    return x * 3\n")

    assert result.outcome is CaseOutcome.PASSED
    assert not result.survived


def test_a_case_beyond_the_reference_takes_the_canonical_s_answer():
    """The ordinary path past the reference's reach, not a failure. The case
    lands, and names the solution that computed it."""
    slow = "def solve(x):\n    import time\n\n    time.sleep(9 if x > 5 else 0)\n    return x + x\n"

    result = checked(([2], 4), ([9], 18), reference=slow, cap_ms=300)

    assert result.survived
    assert [one.args for one in result.cases] == [[2], [9]]
    assert [one.expected for one in result.cases] == [4, 18]
    assert [one.expected_from for one in result.cases] == [
        ExpectedSource.REFERENCE,
        ExpectedSource.CANONICAL,
    ]


def test_a_case_the_reference_computed_names_it():
    """Two cases in a set are not equally strong, and nothing but the field
    says which is which."""
    result = checked(([2], 4))

    assert [one.expected_from for one in result.cases] == [ExpectedSource.REFERENCE]


def test_a_reference_that_computed_no_case_discards_the_problem():
    """Every expected output would be the canonical's own, and `verified`
    would then mean only that the solution agrees with itself."""
    result = checked(([2], 4), reference="def solve(x):\n    raise ValueError(x)\n")

    assert result.discard is Discard.UNTESTED
    assert result.outcome is CaseOutcome.PASSED
    assert result.cases == []


def test_the_run_reports_what_the_canonical_s_slowest_case_took():
    """The mutation loop paces its cap by it, and running the canonical again
    to time it costs a subprocess per case."""
    slow = "import time\n\n\ndef solve(x):\n    time.sleep(0.05)\n    return x * 2\n"

    result = checked(([2], 4), canonical=slow)

    assert result.survived
    assert result.slowest_ms is not None
    assert result.slowest_ms >= 50
