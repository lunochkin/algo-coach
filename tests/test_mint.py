import pytest

from algo_coach.mint import classifier_claim, new_id, self_label, user_claim
from algo_coach.schema import ClaimSource, FailureMode


def test_ids_do_not_repeat():
    assert len({new_id() for _ in range(1000)}) == 1000


def test_an_id_says_nothing_about_the_record():
    """Derived from content, two engines would mint one id for two records."""
    first = user_claim("a1", ["greedy"])
    second = user_claim("a1", ["greedy"])

    assert first.id != second.id


def test_a_user_claim_carries_no_version():
    claim = user_claim("a1", ["greedy", "sorting"])

    assert claim.source is ClaimSource.USER
    assert (claim.model, claim.prompt_version) == (None, None)
    assert claim.techniques == ["greedy", "sorting"]


def test_a_classifier_claim_names_what_produced_it():
    """Both count the same toward progress, but a machine claim can be
    recomputed by a better classifier and a user's cannot, so re-deriving has
    to find the stale ones and leave the rest."""
    claim = classifier_claim("a1", ["greedy"], model="a-model", prompt_version="1")

    assert claim.source is ClaimSource.CLASSIFIER
    assert (claim.model, claim.prompt_version) == ("a-model", "1")


def test_an_unknown_code_is_rejected():
    """The only write path that could introduce one: every other code comes
    from the tag mapping, which draws on the vocabulary already."""
    with pytest.raises(ValueError, match="not-a-technique"):
        classifier_claim("a1", ["not-a-technique"], model="a-model", prompt_version="1")


def test_a_known_code_beside_an_unknown_one_does_not_save_it():
    """A claim names every technique the attempt used, so it lands whole or
    not at all — writing the half that passed would assert a set nobody made."""
    with pytest.raises(ValueError, match="not-a-technique"):
        classifier_claim("a1", ["greedy", "not-a-technique"], model="a-model", prompt_version="1")


def test_naming_nothing_writes_no_claim():
    """An empty verdict leaves the fallback standing; the record has no way to
    say 'none of these' and should not be asked to."""
    with pytest.raises(ValueError):
        classifier_claim("a1", [], model="a-model", prompt_version="1")


def test_a_self_label_is_keyed_to_its_attempt():
    label = self_label("a1", FailureMode.RUST)

    assert (label.attempt_id, label.mode) == ("a1", FailureMode.RUST)


def test_records_are_stamped_when_minted():
    """Created_at is the moment the record was made, not the attempt's."""
    claim = user_claim("a1", ["greedy"])
    label = self_label("a1", FailureMode.GAP)

    assert claim.created_at.tzinfo is not None
    assert label.created_at.tzinfo is not None
