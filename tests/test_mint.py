import pytest
from helpers import machine_claim

from algo_coach.mint import (
    generated_problem,
    machine_match,
    new_id,
    self_label,
    user_claim,
    user_match,
)
from algo_coach.schema import (
    ClaimSource,
    Confidence,
    FailureMode,
    MatchSource,
    ProblemStatus,
)


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
    assert (claim.model, claim.effort, claim.call_id, claim.prompt_hash) == (
        None,
        None,
        None,
        None,
    )
    assert claim.techniques == ["greedy", "sorting"]


def test_a_user_claim_is_blind_by_default():
    """The drill loop asks before any classifier has read the attempt, and a
    hand pass over the backlog is asked from the code and the tags. Both are
    independent, so the caller says otherwise rather than saying so."""
    claim = user_claim("a1", ["greedy"])

    assert (claim.informed_by, claim.confidence) == ([], None)


def test_a_user_claim_records_what_its_author_had_seen():
    """A revision is asked with the readings in view, and a claim that cannot
    say so is scored against the reading that produced it."""
    claim = user_claim("a1", ["greedy"], informed_by=["call-1"])

    assert claim.informed_by == ["call-1"]


def test_a_user_claim_records_how_sure_its_author_was():
    claim = user_claim("a1", ["greedy"], confidence=Confidence.GUESS)

    assert claim.confidence is Confidence.GUESS


def test_a_machine_claim_has_seen_nothing():
    """The classifier reads one attempt's code and candidates, never another
    reading of it — so there is no configuration it is not independent of."""
    assert machine_claim("a1", ["greedy"]).informed_by == []


def test_a_classifier_claim_names_what_produced_it():
    """Both count the same toward progress, but a machine claim can be
    recomputed by a better classifier and a user's cannot, so re-deriving has
    to find the stale ones and leave the rest."""
    claim = machine_claim("a1", ["greedy"])

    assert claim.source is ClaimSource.CLASSIFIER
    assert (claim.model, claim.effort, claim.call_id, claim.prompt_hash) == (
        "a-model",
        "medium",
        "call-1",
        "0123456789ab",
    )


def test_an_unknown_code_is_rejected():
    """The only write path that could introduce one: every other code is drawn
    from the vocabulary already."""
    with pytest.raises(ValueError, match="not-a-technique"):
        machine_claim("a1", ["not-a-technique"])


def test_a_known_code_beside_an_unknown_one_does_not_save_it():
    """A claim names every technique the attempt used, so it lands whole or
    not at all — writing the half that passed would assert a set nobody made."""
    with pytest.raises(ValueError, match="not-a-technique"):
        machine_claim("a1", ["greedy", "not-a-technique"])


def test_naming_nothing_is_a_verdict_the_machine_may_record():
    """The classifier read the code and found the candidates did not cover it.
    Stored, or every later run pays for the same answer; the fallback still
    stands, because the resolver reads an empty set as no answer."""
    claim = machine_claim("a1", [])

    assert claim.techniques == []


def test_naming_nothing_is_not_a_verdict_a_user_may_record():
    """The loop records nothing where they skip, so a bare empty user claim
    would be a lost answer in the shape of a stated one. Saying so is a
    separate field, and this is the case without it."""
    with pytest.raises(ValueError, match="at least one technique"):
        user_claim("a1", [])


def test_a_user_may_decline_by_saying_so():
    """The candidates do not cover what the code did, asserted rather than
    inferred from an empty list. It is what a skip is told apart from."""
    claim = user_claim("a1", [], declined=True)

    assert claim.techniques == []
    assert claim.declined is True
    assert claim.source is ClaimSource.USER


def test_a_claim_naming_techniques_cannot_also_decline():
    """Both at once asserts that the candidates do not apply and names two of
    them. Nothing reading the record could say which was meant."""
    with pytest.raises(ValueError, match="decline"):
        user_claim("a1", ["greedy"], declined=True)


def test_a_machine_decline_needs_no_flag():
    """Its empty set was never ambiguous: the classifier answers or fails, and
    a failure writes no claim. Tightening the field would reach every decline
    already stored."""
    claim = machine_claim("a1", [])

    assert (claim.techniques, claim.declined) == ([], False)


def test_a_self_label_is_keyed_to_its_attempt():
    label = self_label("a1", FailureMode.RUST)

    assert (label.attempt_id, label.mode) == ("a1", FailureMode.RUST)


def test_records_are_stamped_when_minted():
    """Created_at is the moment the record was made, not the attempt's."""
    claim = user_claim("a1", ["greedy"])
    label = self_label("a1", FailureMode.GAP)

    assert claim.created_at.tzinfo is not None
    assert label.created_at.tzinfo is not None


def test_a_hand_match_carries_no_configuration():
    """Nothing re-derives it, which is what makes it the reference a reading is
    scored against."""
    match = user_match("t1", "p1", matched=True)

    assert match.source is MatchSource.USER
    assert [field for field in match.RECORDED if getattr(match, field) is not None] == []
    assert (match.template_id, match.problem_id, match.matched) == ("t1", "p1", True)


def test_a_hand_match_is_blind_by_default():
    """The pool offers a pair whatever a matcher said about it, and the prompt
    shows nothing unless asked — so the caller says otherwise rather than
    saying so."""
    assert user_match("t1", "p1", matched=True).informed_by == []


def test_a_hand_match_records_what_its_author_had_seen():
    """An annotation made with a verdict in view is no longer independent of
    it, and the agreement it is later scored on measures rather less."""
    match = user_match("t1", "p1", matched=True, informed_by=["call-1"])

    assert match.informed_by == ["call-1"]


def test_a_machine_match_has_seen_nothing():
    """The matcher reads one statement against one card's cues, never another
    reading of them."""
    match = machine_match(
        "t1",
        "p1",
        matched=True,
        model="a-model",
        effort="medium",
        prompt_hash="0123456789ab",
        call_id="call-1",
        pin="a-host",
    )

    assert match.informed_by == []


def test_a_hand_match_annotates_the_negative_too():
    """The machine answers every candidate of a card, so a reference naming
    only the matches would score its yes and say nothing about its no."""
    assert user_match("t1", "p1", matched=False).matched is False


def test_a_machine_match_names_what_produced_it():
    match = machine_match(
        "t1",
        "p1",
        matched=True,
        model="a-model",
        effort="medium",
        prompt_hash="0123456789ab",
        call_id="call-1",
        pin="a-host",
        temperature=0.0,
        provider="fake",
    )

    assert match.source is MatchSource.CLASSIFIER
    assert (match.model, match.effort, match.pin, match.prompt_hash, match.call_id) == (
        "a-model",
        "medium",
        "a-host",
        "0123456789ab",
        "call-1",
    )


def generated(**overrides):
    fields = {
        "title": "Two Sum",
        "statement": "Given an array, return ...",
        "generated_for": "t1",
        "model": "a-model",
        "effort": "medium",
        "prompt_hash": "0123456789ab",
        "call_id": "call-1",
        "pin": "a-host",
    } | overrides
    return generated_problem(**fields)


def test_a_generated_problem_names_what_wrote_it():
    """Required unconditionally: generated is a problem's only origin, so
    there is no hand arm to exempt as there is for a claim or a match."""
    problem = generated()

    assert (
        problem.model,
        problem.effort,
        problem.pin,
        problem.prompt_hash,
        problem.call_id,
    ) == ("a-model", "medium", "a-host", "0123456789ab", "call-1")


def test_the_minter_is_what_supplies_provenance():
    """A call site spelling the five fields out could fill them partly, and a
    problem stored that way names a configuration nothing can compare it on."""
    with pytest.raises(TypeError):
        generated_problem("Two Sum", "Given an array, return ...")


def test_a_generated_problem_is_minted_an_id():
    """As every stored record is. Nothing outside the engine supplies one."""
    assert generated().id != generated().id


def test_generation_records_what_it_sampled_at():
    """Sampled rather than greedy, which a reading never is: variance is what
    stops one model's habits becoming the whole corpus."""
    assert generated(temperature=1.0).temperature == 1.0
    assert generated().temperature is None


def test_who_served_a_generated_problem_is_recorded():
    assert generated(provider="fake").provider == "fake"


def test_what_a_generated_problem_cost_is_recorded():
    """A match cannot record this and a claim can. Generation is the expensive
    call of the three, so the corpus says what it was paid for."""
    assert generated(cost=0.02).cost == 0.02


def test_a_generated_problem_starts_with_no_techniques():
    """A view over its canonical solutions, and none is written yet."""
    assert generated().techniques == []


def test_the_techniques_are_passed_rather_than_read_here():
    """The canonical is written in the same act, so what it used is known by
    the time the problem is minted."""
    assert generated(techniques=["greedy"]).techniques == ["greedy"]


def test_a_generated_problem_asserts_the_template_it_was_written_for():
    """What the generator was told, not what a matcher inferred. That is what
    makes the first `TemplateMatch` on the pair provenance rather than a
    reading, and it asserts nothing about the forms the problem also
    exercises."""
    assert generated(generated_for="t7").generated_for == "t7"


def test_a_problem_from_a_technique_brief_names_no_template():
    """A brief naming a skill rather than a form told the generator no pair to
    assert. What such a problem is about comes from its canonicals."""
    assert generated(generated_for=None).generated_for is None


def test_a_generated_problem_is_created_rather_than_served():
    """Landing is not clearing. Retirement is a judgement made later still, so
    generation has no say in either and takes no argument for them."""
    assert generated().status is ProblemStatus.CREATED
    assert generated().retired_reason is None
    with pytest.raises(TypeError):
        generated(status="active")
