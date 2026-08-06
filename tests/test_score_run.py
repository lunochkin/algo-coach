from datetime import timedelta

import pytest
from helpers import T0, FakeClient, Verdict, attempt, machine_claim, seed_problem

from algo_coach.claims import EFFORT, MODEL, PROMPT_HASH, PROMPT_VERSION, score_backlog
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import ClaimSource
from algo_coach.techniques import standing_claims


def reading(attempt_id: str, techniques: list[str], **configuration):
    """A stored reading at this classifier's configuration unless a test names
    the field it differs in."""
    return machine_claim(
        attempt_id,
        techniques,
        **{
            "model": MODEL,
            "effort": EFFORT,
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": PROMPT_HASH,
        }
        | configuration,
    )


@pytest.fixture
def hand_claimed(tmp_path) -> AttemptLog:
    """One two-tag problem, one attempt on it, the user's claim standing."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(user_claim("a1", ["greedy"]))
    return log


@pytest.fixture
def two_problems(tmp_path) -> AttemptLog:
    """A hand claim on each of two problems, so neither collapses into the
    other and a run has two attempts to spend a call on."""
    root = tmp_path / "data"
    seed_problem(root, id="p1", tags=["Greedy", "Sorting"])
    seed_problem(root, id="p2", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "p1", finished_at=T0))
    log.append_attempt(attempt("a2", "p2", finished_at=T0 + timedelta(days=1)))
    log.append_claim(user_claim("a1", ["greedy"]))
    log.append_claim(user_claim("a2", ["greedy"]))
    return log


def run(client, log, **kwargs):
    problems = {problem.id: problem for problem in ProblemStore(log.root).all()}
    return score_backlog(client, log, problems, user_id="u1", **kwargs)


def machine_claims(log):
    return [claim for claim in log.claims() if claim.source is ClaimSource.CLASSIFIER]


def test_agreement_is_scored_against_the_users_claim(hand_claimed):
    result = run(FakeClient.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.scored, result.exact) == (1, 1)


def test_disagreement_is_scored_per_technique(hand_claimed):
    result = run(FakeClient.answering(Verdict(["sorting"])), hand_claimed)

    rows = {row.technique: row for row in result.per_technique}
    assert (result.scored, result.exact) == (1, 0)
    assert (rows["greedy"].attempts, rows["greedy"].exact) == (1, 0)
    assert rows["sorting"].over == 1


def test_what_the_classifier_read_is_stored(hand_claimed):
    """An eval that forgot its verdicts would be evidence that exists only
    while it prints."""
    run(FakeClient.answering(Verdict(["sorting"])), hand_claimed)

    (stored,) = machine_claims(hand_claimed)
    assert (stored.attempt_id, stored.techniques) == ("a1", ["sorting"])
    assert (stored.model, stored.effort, stored.prompt_version, stored.prompt_hash) == (
        MODEL,
        EFFORT,
        PROMPT_VERSION,
        PROMPT_HASH,
    )


def test_a_stored_reading_never_becomes_the_standing_claim(hand_claimed):
    """It is a reading, not a candidate: the user's claim wins by source, not
    by being the later record."""
    run(FakeClient.answering(Verdict(["sorting"])), hand_claimed)

    standing = standing_claims(hand_claimed.claims())["a1"]
    assert [claim.techniques for claim in machine_claims(hand_claimed)] == [["sorting"]]
    assert (standing.source, standing.techniques) == (ClaimSource.USER, ["greedy"])


def test_a_second_run_at_this_configuration_pays_for_nothing(hand_claimed):
    """The same question of the same classifier has an answer in the log."""
    run(FakeClient.answering(Verdict(["greedy"])), hand_claimed)
    client = FakeClient.answering()

    result = run(client, hand_claimed)

    assert (result.scored, result.exact) == (1, 1)
    assert (result.read, result.reused, client.messages.calls) == (0, 1, [])


def test_a_reading_stored_before_the_hand_claim_is_reused(tmp_path):
    """The ordinary correction path: the backlog run claims, the user corrects.
    Scoring that attempt is already paid for."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(reading("a1", ["sorting"]))
    log.append_claim(user_claim("a1", ["greedy"]))
    client = FakeClient.answering()

    result = run(client, log)

    assert (result.scored, result.exact, result.reused) == (1, 0, 1)
    assert client.messages.calls == []


def test_a_rolled_back_configuration_reuses_its_own_reading(hand_claimed):
    """Running an earlier prompt on purpose is a rollback, so this
    configuration's reading can sit under a later one's and still answer."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))
    hand_claimed.append_claim(reading("a1", ["sorting"], prompt_version="0"))
    client = FakeClient.answering()

    result = run(client, hand_claimed)

    assert (result.exact, result.reused, client.messages.calls) == (1, 1, [])


def test_a_reading_from_an_older_prompt_version_is_read_again(hand_claimed):
    hand_claimed.append_claim(reading("a1", ["sorting"], prompt_version="0"))

    result = run(FakeClient.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.read, result.reused, result.exact) == (1, 0, 1)


def test_a_reading_from_another_model_is_read_again(hand_claimed):
    hand_claimed.append_claim(reading("a1", ["sorting"], model="an-older-model"))

    result = run(FakeClient.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.read, result.exact) == (1, 1)


def test_a_reading_differing_only_in_prompt_hash_is_reused(hand_claimed):
    """The hash marks nothing — only the author's version bump says the reading
    changed, and a reflowed sentence must not re-read the eval set."""
    hand_claimed.append_claim(reading("a1", ["greedy"], prompt_hash="ffffffffffff"))
    client = FakeClient.answering()

    result = run(client, hand_claimed)

    assert (result.reused, client.messages.calls) == (1, [])


def test_a_reused_reading_from_another_prompt_text_is_reported(hand_claimed):
    """Two hashes under one version are a forgotten bump. Reuse keys off the
    version, so the divergence the hash exists to expose is the one reuse would
    otherwise bury."""
    hand_claimed.append_claim(reading("a1", ["greedy"], prompt_hash="ffffffffffff"))

    result = run(FakeClient.answering(), hand_claimed)

    assert (result.reused, result.rehashed) == (1, 1)


def test_naming_no_candidate_is_undecided_rather_than_a_total_miss(hand_claimed):
    """No verdict is missing evidence, not a disagreement — scoring it as one
    would count a decline as a wrong answer against every technique."""
    result = run(FakeClient.answering(Verdict([])), hand_claimed)

    assert (result.scored, result.undecided) == (0, 1)
    assert machine_claims(hand_claimed) == []


def test_a_reading_that_named_no_candidate_is_paid_for_on_every_run(hand_claimed):
    """A claim cannot say "none of these", so nothing records that it was
    asked. The count is what says the call is a permanent line item."""
    run(FakeClient.answering(Verdict([])), hand_claimed)
    client = FakeClient.answering(Verdict([]))

    result = run(client, hand_claimed)

    assert (result.undecided, len(client.messages.calls)) == (1, 1)


def test_a_failed_reading_stores_nothing(hand_claimed):
    result = run(FakeClient.answering(Verdict(error=RuntimeError("refused"))), hand_claimed)

    assert [failure.attempt_id for failure in result.failed] == ["a1"]
    assert (result.scored, machine_claims(hand_claimed)) == (0, [])


def test_a_machine_claim_is_not_ground_truth(tmp_path):
    """The eval scores one against the other, so an attempt the classifier
    already claimed answers nothing."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(machine_claim("a1", ["greedy"]))

    client = FakeClient.answering()
    result = run(client, log)

    assert (result.scored, client.messages.calls) == (0, [])


def test_an_unclaimed_attempt_is_not_scored(tmp_path):
    """Nothing to score it against — the hand pass has not reached it."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))

    client = FakeClient.answering()

    assert (run(client, log).scored, client.messages.calls) == (0, [])


def test_only_the_latest_attempt_of_a_problem_is_scored(tmp_path):
    """A retry asks the identical question, so counting both would weight that
    problem twice."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("older", "two-tags", finished_at=T0))
    log.append_attempt(attempt("latest", "two-tags", finished_at=T0 + timedelta(days=1)))
    log.append_claim(user_claim("older", ["greedy"]))
    log.append_claim(user_claim("latest", ["sorting"]))

    result = run(FakeClient.answering(Verdict(["sorting"])), log)

    assert (result.scored, result.exact, result.failed) == (1, 1, [])


def test_one_failure_does_not_cost_the_rest(two_problems):
    """An eval that dies on the first refusal reports nothing about the rest."""
    result = run(
        FakeClient.answering(Verdict(error=RuntimeError("refused")), Verdict(["greedy"])),
        two_problems,
    )

    assert (result.scored, result.exact) == (1, 1)
    assert [failure.attempt_id for failure in result.failed] == ["a2"]


def test_the_limit_caps_the_calls_not_the_score(two_problems):
    """A stored reading is free, so a capped run adds to what earlier runs read
    rather than reporting on a slice of it."""
    two_problems.append_claim(reading("a2", ["greedy"]))
    client = FakeClient.answering(Verdict(["greedy"]))

    result = run(client, two_problems, limit=1)

    assert (result.scored, result.exact) == (2, 2)
    assert (result.read, result.reused, len(client.messages.calls)) == (1, 1, 1)
