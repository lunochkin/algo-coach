import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach import mint
from algo_coach.schema import ExpectedSource, TestCase


def case(*args, **overrides) -> TestCase:
    """The minter with a configuration spread over it, so a test naming none is
    about the case rather than about what proposed it."""
    return mint.case(*args, **(PROVENANCE | overrides))


def test_a_case_is_keyed_to_a_problem():
    """It has no meaning apart from one, and nothing shares a case between
    problems."""
    assert case("p1", [1], 2).problem_id == "p1"


def test_a_case_naming_no_problem_is_rejected():
    with pytest.raises(ValidationError, match="problem_id"):
        TestCase(id="c1", problem_id="", args=[], expected=1)


def test_a_case_is_arguments_and_an_expected_return():
    """Not a transcript. Parsing stdin would make a case describe how a
    solution was driven rather than what it must compute."""
    one = case("p1", [[2, 7, 11, 15], 9], [0, 1])

    assert (one.args, one.expected) == ([[2, 7, 11, 15], 9], [0, 1])


def test_a_case_may_pass_no_arguments():
    """A problem may ask for a function of none, and such a case still decides
    the solution."""
    assert case("p1", [], 42).args == []


def test_a_case_must_say_what_it_expects():
    """One without an expected return decides nothing, so absence is rejected
    rather than defaulted."""
    with pytest.raises(ValidationError, match="expected"):
        TestCase(id="c1", problem_id="p1", args=[1])


def test_none_is_an_expected_return_rather_than_an_absence():
    """A solution may legitimately return it, which is why a missing field
    cannot stand in for one."""
    assert case("p1", [1], None).expected is None


def test_a_case_is_minted_an_id():
    """As every stored record is. Nothing outside the engine supplies one."""
    assert case("p1", [1], 2).id != case("p1", [1], 2).id


def test_a_case_names_the_call_that_proposed_its_arguments():
    """Not the problem's own call: a mutation round and the speedup search each
    propose arguments at their own configuration."""
    one = case("p1", [1], 2, call_id="round-2")

    assert (one.call_id, one.model) == ("round-2", "a-model")


def test_a_case_missing_part_of_its_configuration_is_rejected():
    """All of it or none, as every machine record. A case whose configuration
    is partly unknown compares with nothing."""
    with pytest.raises(ValidationError, match="needs pin"):
        TestCase(
            id="c1",
            problem_id="p1",
            args=[1],
            expected=2,
            expected_from=ExpectedSource.REFERENCE,
            round=0,
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
        )


def test_a_case_names_the_round_that_won_it():
    """Zero is the set written with the statement, which is what the mutation
    loop was first run against."""
    assert (case("p1", [1], 2).round, case("p1", [1], 2, round=2).round) == (0, 2)


def test_a_case_no_round_won_and_the_statement_did_not_write_carries_none():
    """The separating case is appended after the loop, so a replay rebuilding
    the set the survivors were decided against leaves it out."""
    assert case("p1", [10**6], 3, round=None).round is None


def test_a_case_that_names_no_round_is_rejected():
    """A model default would answer for a writer that never considered which
    call put the case in the set. The minter answers it once."""
    with pytest.raises(ValidationError, match="round"):
        TestCase(
            id="c1",
            problem_id="p1",
            args=[1],
            expected=2,
            expected_from=ExpectedSource.REFERENCE,
            **PROVENANCE,
        )


def test_a_case_names_where_its_expected_output_came_from():
    """The reference computes them wherever it reaches, and beyond its reach
    only the canonical can. A case the canonical answered is evidence about the
    cap rather than about the verdict, and nothing but this field says so."""
    at_scale = case("p1", [10**6], 3, expected_from=ExpectedSource.CANONICAL)

    assert at_scale.expected_from is ExpectedSource.CANONICAL


def test_expected_outputs_come_from_the_reference_unless_a_case_says_otherwise():
    """It is different code from a call that saw the statement alone, so a case
    it computed is a test. One the canonical answered passes by construction."""
    assert case("p1", [1], 2).expected_from is ExpectedSource.REFERENCE


def test_a_case_that_names_no_source_is_rejected():
    """Two cases in a set are not equally strong evidence. A model default
    would answer for a writer that never considered the question; the minter
    answers it once, where the rule is written down."""
    with pytest.raises(ValidationError, match="expected_from"):
        TestCase(id="c1", problem_id="p1", args=[1], expected=2)


def test_a_case_survives_the_store_round_trip():
    """Arguments and returns are whatever the problem asks for, so they have
    to reach JSON and come back unchanged."""
    one = case("p1", [[2, 7], {"k": 1}, "s", 1.5, True, None], [0, 1])

    assert TestCase.model_validate_json(one.model_dump_json()) == one
