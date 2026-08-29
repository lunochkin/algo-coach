"""A test case: one call of a solution, and what it must return.

Written with the problem rather than after it. What enforces that is the act
that writes them, not this model — cases derived from a finished solution
describe whatever it happens to do, where cases written with the statement
describe what the problem asks.
"""

import pytest
from pydantic import ValidationError

from algo_coach.mint import case
from algo_coach.schema import Problem, TestCase


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


def test_a_case_carries_no_provenance():
    """It is not a reading. The problem it is keyed to already names the
    configuration that wrote both in one call."""
    assert not [name for name in TestCase.model_fields if name in Problem.RECORDED]


def test_a_case_survives_the_store_round_trip():
    """Arguments and returns are whatever the problem asks for, so they have
    to reach JSON and come back unchanged."""
    one = case("p1", [[2, 7], {"k": 1}, "s", 1.5, True, None], [0, 1])

    assert TestCase.model_validate_json(one.model_dump_json()) == one
