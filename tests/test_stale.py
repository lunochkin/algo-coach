"""The configuration comparison itself, rather than through a backlog run.

Two readers depend on it now: the write path skips what it has already
derived, and the eval reuses what it has already paid to read.
"""

from helpers import CONFIGURATION, machine_claim

from algo_coach.claims import at_configuration, is_stale, readings_at
from algo_coach.mint import user_claim


def test_a_claim_at_this_configuration_is_read_as_current():
    assert at_configuration(machine_claim("a1", ["greedy"]), CONFIGURATION)


def test_a_user_claim_is_at_no_configuration():
    """It names nothing that produced it: nothing re-derives it, and nothing
    reuses it as a reading of its own."""
    claim = user_claim("a1", ["greedy"])

    assert not at_configuration(claim, CONFIGURATION)
    assert not is_stale(claim, CONFIGURATION)


def test_a_claim_from_another_prompt_version_is_at_another_configuration():
    claim = machine_claim("a1", ["greedy"], prompt_version="0")

    assert not at_configuration(claim, CONFIGURATION)
    assert is_stale(claim, CONFIGURATION)


def test_a_claim_differing_only_in_prompt_hash_is_at_this_configuration():
    """The version is the semantic boundary, the hash the syntactic one."""
    claim = machine_claim("a1", ["greedy"], prompt_hash="ffffffffffff")

    assert at_configuration(claim, CONFIGURATION)


def test_the_readings_are_this_configurations_own_latest():
    older = machine_claim("a1", ["greedy"])
    newer = machine_claim("a1", ["sorting"])

    assert readings_at([older, newer], CONFIGURATION)["a1"].techniques == ["sorting"]


def test_a_later_claim_from_another_configuration_hides_nothing():
    """Filtered before the latest is taken, never after: an earlier prompt run
    on purpose is a rollback, and the reading under it still answers."""
    mine = machine_claim("a1", ["greedy"])
    theirs = machine_claim("a1", ["sorting"], prompt_version="0")

    assert readings_at([mine, theirs], CONFIGURATION)["a1"].techniques == ["greedy"]


def test_a_user_claim_is_not_a_reading():
    assert readings_at([user_claim("a1", ["greedy"])], CONFIGURATION) == {}
