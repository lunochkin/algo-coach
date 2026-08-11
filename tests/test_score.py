from algo_coach.claims import score
from algo_coach.claims.score import per_decision


def rows(result):
    return {row.technique: row for row in result.per_technique}


def test_a_matching_set_scores_exact():
    result = score({"a1": ["greedy", "sorting"]}, {"a1": ["sorting", "greedy"]})

    assert (result.scored, result.exact) == (1, 1)


def test_a_missing_technique_is_not_a_match():
    """Set equality, not overlap: a claim naming one of two decided half the
    question, and the board reads the whole set."""
    result = score({"a1": ["greedy", "sorting"]}, {"a1": ["greedy"]})

    assert (result.scored, result.exact) == (1, 0)


def test_naming_every_candidate_does_not_pass():
    """It agrees with the tags and decides nothing — the failure a metric
    asking only whether the right code appears would miss."""
    result = score({"a1": ["greedy"]}, {"a1": ["greedy", "sorting"]})

    assert result.exact == 0


def test_a_technique_carries_the_attempts_the_user_named_it_on():
    result = score(
        {"a1": ["greedy"], "a2": ["greedy", "sorting"]},
        {"a1": ["greedy"], "a2": ["greedy"]},
    )

    assert (rows(result)["greedy"].attempts, rows(result)["greedy"].exact) == (2, 1)
    assert (rows(result)["sorting"].attempts, rows(result)["sorting"].exact) == (1, 0)


def test_over_claiming_is_counted_against_the_technique_it_added():
    """Per technique rather than overall, since a classifier that over-claims
    one code skews the board wherever that code is read."""
    result = score({"a1": ["greedy"]}, {"a1": ["greedy", "sorting"]})

    assert rows(result)["sorting"].over == 1
    assert rows(result)["greedy"].over == 0


def test_a_technique_the_classifier_left_out_is_counted_as_missed():
    """The other asymmetric failure: over-claiming and under-claiming want
    opposite fixes, and set equality alone tells them apart nowhere."""
    result = score({"a1": ["greedy", "sorting"]}, {"a1": ["greedy"]})

    assert (rows(result)["sorting"].missed, rows(result)["sorting"].over) == (1, 0)
    assert rows(result)["greedy"].missed == 0


def test_a_wrong_set_naming_the_technique_is_not_a_miss():
    """`exact` already carries it — a miss is the classifier not naming the
    code, not naming it beside something wrong."""
    result = score({"a1": ["greedy"]}, {"a1": ["greedy", "sorting"]})

    assert (rows(result)["greedy"].exact, rows(result)["greedy"].missed) == (0, 0)


def test_every_disagreement_is_returned():
    """Reviewing them is how a mislabelled hand claim is caught: the eval
    measures agreement, and only a reader can say which side was wrong."""
    result = score(
        {"a1": ["greedy"], "a2": ["sorting"]},
        {"a1": ["greedy"], "a2": ["trie", "greedy"]},
    )

    (disagreement,) = result.disagreements
    assert disagreement.attempt_id == "a2"
    assert (disagreement.user, disagreement.machine) == (["sorting"], ["greedy", "trie"])


def test_a_technique_the_user_never_named_still_gets_a_row():
    """Otherwise the code the classifier reaches for wrongly is the one code
    the score cannot see."""
    result = score({"a1": ["greedy"]}, {"a1": ["trie"]})

    assert rows(result)["trie"].attempts == 0
    assert rows(result)["trie"].over == 1


def test_an_attempt_with_no_machine_verdict_is_not_scored():
    """A failed call is missing evidence, not a disagreement."""
    result = score({"a1": ["greedy"], "a2": ["sorting"]}, {"a1": ["greedy"]})

    assert (result.scored, result.exact) == (1, 1)


def test_duplicates_do_not_change_the_verdict():
    result = score({"a1": ["greedy"]}, {"a1": ["greedy", "greedy"]})

    assert result.exact == 1


def test_the_rows_are_ordered_by_technique():
    result = score({"a1": ["sorting", "greedy"]}, {"a1": ["sorting", "greedy"]})

    assert [row.technique for row in result.per_technique] == ["greedy", "sorting"]


def test_per_decision_counts_every_candidate_not_every_claim():
    """Declining a code correctly is a decision the classifier made, and the
    one set equality never credits."""
    total, agreed = per_decision(
        {"a1": ["greedy"]},
        {"a1": ["greedy"]},
        {"a1": ["greedy", "sorting", "hashing"]},
    )

    assert (total, agreed) == (3, 3)


def test_per_decision_charges_one_call_per_wrong_candidate():
    """A missed code and an over-claimed one are one wrong decision each, so a
    set wrong in two places scores worse than one wrong in a single place."""
    total, agreed = per_decision(
        {"a1": ["greedy"]},
        {"a1": ["sorting"]},
        {"a1": ["greedy", "sorting", "hashing"]},
    )

    assert (total, agreed) == (3, 1)


def test_per_decision_ignores_a_code_the_candidates_no_longer_offer():
    """A stored reading can carry a code the tag mapping has stopped deriving.
    An attempt's decisions must never outnumber the choices it offered."""
    total, agreed = per_decision(
        {"a1": ["greedy"]},
        {"a1": ["greedy", "retired-code"]},
        {"a1": ["greedy", "sorting"]},
    )

    assert (total, agreed) == (2, 2)


def test_per_decision_skips_an_attempt_with_no_candidates():
    """A problem whose tags reach no code offers no decision — counted at zero
    it would drag every rate toward zero for a call nobody made."""
    total, agreed = per_decision({"a1": ["greedy"]}, {"a1": ["greedy"]}, {})

    assert (total, agreed) == (0, 0)


def test_per_decision_skips_what_the_classifier_did_not_read():
    total, agreed = per_decision(
        {"a1": ["greedy"], "a2": ["sorting"]},
        {"a1": ["greedy"]},
        {"a1": ["greedy", "sorting"], "a2": ["greedy", "sorting"]},
    )

    assert (total, agreed) == (2, 2)
