from datetime import timedelta

import pytest
from helpers import T0, FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import MODEL, PROMPT_VERSION, ClassifierError, classify_backlog
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import ClaimSource, TechniqueClaim

answering = FakeClient.answering


@pytest.fixture
def backlog(tmp_path, monkeypatch) -> AttemptLog:
    """One two-tag problem and one single-tag problem, an attempt on each."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    seed_problem(root, id="one-tag", tags=["Trie"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_attempt(attempt("a2", "one-tag"))
    return log


def stored(log: AttemptLog):
    return {problem.id: problem for problem in ProblemStore(log.root).all()}


def run(client, log, **kwargs):
    return classify_backlog(client, log, stored(log), user_id="u1", **kwargs)


def test_a_verdict_is_written_as_a_classifier_claim(backlog):
    client = answering(Verdict(["greedy"]))

    result = run(client, backlog)

    (claim,) = backlog.claims()
    assert claim.attempt_id == "a1"
    assert claim.techniques == ["greedy"]
    assert claim.source is ClaimSource.CLASSIFIER
    assert (claim.model, claim.prompt_version) == (MODEL, PROMPT_VERSION)
    assert result.classified == 1


def test_a_single_tag_problem_is_never_asked_about(backlog):
    """Its fallback already answers; a claim there disputes nothing, and it
    would cost a call to agree with the tags."""
    client = answering(Verdict(["greedy"]))

    run(client, backlog)

    assert [claim.attempt_id for claim in backlog.claims()] == ["a1"]
    assert len(client.messages.calls) == 1


def test_an_attempt_without_code_is_never_asked_about(tmp_path, monkeypatch):
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags", code=None))

    result = run(answering(), log)

    assert (result.classified, log.claims()) == (0, [])


def test_a_claimed_attempt_is_not_asked_again(backlog):
    """The user claims first and the classifier fills the rest, so a hand
    claim is never overwritten by a machine one."""
    backlog.append_claim(
        TechniqueClaim(
            id="c1",
            created_at=T0,
            attempt_id="a1",
            techniques=["sorting"],
            source=ClaimSource.USER,
        )
    )
    client = answering()

    result = run(client, backlog)

    assert (result.classified, client.messages.calls) == (0, [])


def test_a_run_resumes_where_the_last_one_stopped(tmp_path, monkeypatch):
    """Claims land as they are made and a claimed attempt drops out, so the
    backlog is not paid for twice."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags", finished_at=T0))
    log.append_attempt(attempt("a2", "two-tags", finished_at=T0 + timedelta(days=1)))

    run(answering(Verdict(["greedy"])), log, limit=1)
    run(answering(Verdict(["sorting"])), log, limit=1)

    assert sorted(claim.attempt_id for claim in log.claims()) == ["a1", "a2"]


def test_the_newest_attempts_are_claimed_first(tmp_path, monkeypatch):
    """A run cut short by `limit` improves the numbers the board is showing."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("old", "two-tags", finished_at=T0))
    log.append_attempt(attempt("new", "two-tags", finished_at=T0 + timedelta(days=1)))

    run(answering(Verdict(["greedy"])), log, limit=1)

    assert [claim.attempt_id for claim in log.claims()] == ["new"]


def test_naming_no_candidate_writes_nothing(backlog):
    """A claim cannot say 'none of these', and the fallback already answers
    what the tags say."""
    result = run(answering(Verdict([])), backlog)

    assert (result.classified, result.undecided, backlog.claims()) == (0, 1, [])


def test_one_failure_does_not_cost_the_attempts_behind_it(tmp_path, monkeypatch):
    """A refusal, a rate limit or a dropped connection is one attempt's
    problem; a backlog run must not lose the rest."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags", finished_at=T0))
    log.append_attempt(attempt("a2", "two-tags", finished_at=T0 + timedelta(days=1)))

    result = run(
        answering(Verdict(error=ClassifierError("no verdict: refusal")), Verdict(["greedy"])),
        log,
    )

    assert result.classified == 1
    assert [failure.attempt_id for failure in result.failed] == ["a2"]
    assert [claim.attempt_id for claim in log.claims()] == ["a1"]


def test_the_technique_flag_narrows_the_backlog(backlog):
    seed_problem(backlog.root, id="tries", tags=["Trie", "Sorting"])
    backlog.append_attempt(attempt("a3", "tries"))

    run(answering(Verdict(["trie"])), backlog, technique="trie")

    assert [claim.attempt_id for claim in backlog.claims()] == ["a3"]
