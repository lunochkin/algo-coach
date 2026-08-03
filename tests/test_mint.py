from algo_coach.mint import new_id, self_label, user_claim
from algo_coach.schema import ClaimSource, FailureMode


def test_ids_do_not_repeat():
    assert len({new_id() for _ in range(1000)}) == 1000


def test_an_id_says_nothing_about_the_record():
    """Derived from content, two engines would mint one id for two records."""
    first = user_claim("a1", ["greedy"])
    second = user_claim("a1", ["greedy"])

    assert first.id != second.id
    assert "a1" not in first.id


def test_a_user_claim_carries_no_version():
    claim = user_claim("a1", ["greedy", "sorting"])

    assert claim.source is ClaimSource.USER
    assert (claim.model, claim.prompt_version) == (None, None)
    assert claim.techniques == ["greedy", "sorting"]


def test_a_self_label_is_keyed_to_its_attempt():
    label = self_label("a1", FailureMode.RUST)

    assert (label.attempt_id, label.mode) == ("a1", FailureMode.RUST)


def test_records_are_stamped_when_minted():
    """Created_at is the moment the record was made, not the attempt's."""
    claim = user_claim("a1", ["greedy"])
    label = self_label("a1", FailureMode.GAP)

    assert claim.created_at.tzinfo is not None
    assert label.created_at.tzinfo is not None
