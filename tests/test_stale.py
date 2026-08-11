"""The configuration comparison itself, rather than through a backlog run.

Two readers depend on it now: the write path skips what it has already
derived, and the eval reuses what it has already paid to read.
"""

from helpers import CONFIGURATION, PROMPT_HASH, machine_claim

from algo_coach.claims import at_configuration, is_stale, readings_at
from algo_coach.mint import user_claim


def test_a_claim_at_this_configuration_is_read_as_current():
    assert at_configuration(machine_claim("a1", ["greedy"]), CONFIGURATION, PROMPT_HASH)


def test_a_user_claim_is_at_no_configuration():
    """It names nothing that produced it: nothing re-derives it, and nothing
    reuses it as a reading of its own."""
    claim = user_claim("a1", ["greedy"])

    assert not at_configuration(claim, CONFIGURATION, PROMPT_HASH)
    assert not is_stale(claim, CONFIGURATION, PROMPT_HASH)


def test_a_claim_answering_another_prompt_is_stale():
    """Which is the whole rule: a criterion travels with its candidate, so an
    edit reaches the attempts carrying that code and no others."""
    claim = machine_claim("a1", ["greedy"], prompt_hash="ffffffffffff")

    assert not at_configuration(claim, CONFIGURATION, PROMPT_HASH)
    assert is_stale(claim, CONFIGURATION, PROMPT_HASH)


def test_a_claim_from_another_model_is_at_another_configuration():
    claim = machine_claim("a1", ["greedy"], model="another-model")

    assert not at_configuration(claim, CONFIGURATION, PROMPT_HASH)
    assert is_stale(claim, CONFIGURATION, PROMPT_HASH)


def test_an_attempt_with_no_question_matches_nothing():
    """Nothing to compare against, so a reading of it cannot be current."""
    assert readings_at([machine_claim("a1", ["greedy"])], CONFIGURATION, {}) == {}


def test_the_readings_are_this_configurations_own_latest():
    older = machine_claim("a1", ["greedy"])
    newer = machine_claim("a1", ["sorting"])

    assert readings_at([older, newer], CONFIGURATION, {"a1": PROMPT_HASH})["a1"].techniques == [
        "sorting"
    ]


def test_a_later_claim_from_another_configuration_hides_nothing():
    """Filtered before the latest is taken, never after: an earlier prompt run
    on purpose is a rollback, and the reading under it still answers."""
    mine = machine_claim("a1", ["greedy"])
    theirs = machine_claim("a1", ["sorting"], prompt_hash="ffffffffffff")

    assert readings_at([mine, theirs], CONFIGURATION, {"a1": PROMPT_HASH})["a1"].techniques == [
        "greedy"
    ]


def test_a_user_claim_is_not_a_reading():
    assert readings_at([user_claim("a1", ["greedy"])], CONFIGURATION, {"a1": PROMPT_HASH}) == {}
