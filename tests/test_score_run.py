import pytest
from helpers import FakeClient, Verdict, attempt, machine_claim, seed_problem

from algo_coach.claims import score_backlog
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore


@pytest.fixture
def hand_claimed(tmp_path) -> AttemptLog:
    """One two-tag problem, one attempt on it, the user's claim standing."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(user_claim("a1", ["greedy"]))
    return log


def run(client, log, **kwargs):
    problems = {problem.id: problem for problem in ProblemStore(log.root).all()}
    return score_backlog(client, log, problems, user_id="u1", **kwargs)


def test_agreement_is_scored_against_the_users_claim(hand_claimed):
    result = run(FakeClient.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.scored, result.exact) == (1, 1)


def test_disagreement_is_scored_per_technique(hand_claimed):
    result = run(FakeClient.answering(Verdict(["sorting"])), hand_claimed)

    rows = {row.technique: row for row in result.per_technique}
    assert (result.scored, result.exact) == (1, 0)
    assert (rows["greedy"].attempts, rows["greedy"].exact) == (1, 0)
    assert rows["sorting"].over == 1


def test_scoring_writes_nothing(hand_claimed):
    """A machine claim would be the later record, and the latest wins on read —
    the classifier would supersede the evidence it is measured against."""
    before = hand_claimed.claims()

    run(FakeClient.answering(Verdict(["sorting"])), hand_claimed)

    assert hand_claimed.claims() == before


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


def test_one_failure_does_not_cost_the_rest(tmp_path):
    """An eval that dies on the first refusal reports nothing about the rest."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_attempt(attempt("a2", "two-tags"))
    log.append_claim(user_claim("a1", ["greedy"]))
    log.append_claim(user_claim("a2", ["greedy"]))

    result = run(
        FakeClient.answering(Verdict(error=RuntimeError("refused")), Verdict(["greedy"])),
        log,
    )

    assert (result.scored, result.exact) == (1, 1)
    assert [failure.attempt_id for failure in result.failed] == ["a2"]


def test_the_limit_caps_the_run(hand_claimed):
    hand_claimed.append_attempt(attempt("a2", "two-tags"))
    hand_claimed.append_claim(user_claim("a2", ["sorting"]))
    client = FakeClient.answering(Verdict(["greedy"]))

    result = run(client, hand_claimed, limit=1)

    assert (result.scored, len(client.messages.calls)) == (1, 1)
