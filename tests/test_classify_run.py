from datetime import timedelta

import pytest
from helpers import T0, FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import MODEL, PROMPT_VERSION, ClassifierError, classify_backlog
from algo_coach.claims.run import ABORT_AFTER
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.mint import classifier_claim
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


def backlog_of(root, count: int) -> AttemptLog:
    """`count` attempts on one two-tag problem, oldest first — so a verdict
    script reads in the order the run asks, which is newest first."""
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    for age in reversed(range(count)):
        log.append_attempt(attempt(f"a{age}", "two-tags", finished_at=T0 + timedelta(days=-age)))
    return log


def broken() -> Verdict:
    return Verdict(error=RuntimeError("bad key"))


def test_a_run_aborts_once_failures_stop_being_one_attempt_s_problem(tmp_path):
    """A key that does not work, a spent quota or a network that is down fails
    every attempt identically. The run stops rather than paying the same error
    once per attempt in the backlog."""
    log = backlog_of(tmp_path / "data", ABORT_AFTER + 3)
    client = answering(*[broken()] * (ABORT_AFTER + 3))

    result = run(client, log)

    assert result.aborted
    assert len(client.messages.calls) == ABORT_AFTER
    assert len(result.failed) == ABORT_AFTER
    assert log.claims() == []


def test_a_success_resets_the_count(tmp_path):
    """Consecutive, not cumulative: a refusal here and a rate limit there is a
    run that is working."""
    log = backlog_of(tmp_path / "data", ABORT_AFTER * 2)
    client = answering(*[broken(), Verdict(["greedy"])] * ABORT_AFTER)

    result = run(client, log)

    assert not result.aborted
    assert (result.classified, len(result.failed)) == (ABORT_AFTER, ABORT_AFTER)
    assert len(client.messages.calls) == ABORT_AFTER * 2


def test_an_undecided_verdict_resets_the_count(tmp_path):
    """Naming no candidate writes nothing, but the call was answered — the
    classifier is reachable and the run is not broken."""
    log = backlog_of(tmp_path / "data", ABORT_AFTER * 2)
    client = answering(*[broken(), Verdict([])] * ABORT_AFTER)

    result = run(client, log)

    assert (result.aborted, result.undecided) == (False, ABORT_AFTER)


def test_an_aborted_run_keeps_what_landed_before_it(tmp_path):
    """Claims are appended as they are made, so the abort costs the attempts
    behind it and nothing in front."""
    log = backlog_of(tmp_path / "data", ABORT_AFTER + 2)
    client = answering(Verdict(["greedy"]), *[broken()] * ABORT_AFTER)

    result = run(client, log)

    assert (result.aborted, result.classified) == (True, 1)
    assert [claim.attempt_id for claim in log.claims()] == ["a0"]


def test_a_backlog_shorter_than_the_threshold_never_aborts(tmp_path):
    """Nothing to abort in front of: the failures are reported as they always
    were, and the exit code says the run landed nothing."""
    log = backlog_of(tmp_path / "data", ABORT_AFTER - 1)
    client = answering(*[broken()] * (ABORT_AFTER - 1))

    result = run(client, log)

    assert (result.aborted, len(result.failed)) == (False, ABORT_AFTER - 1)


def machine_claim(log, attempt_id, *, model=MODEL, prompt_version=PROMPT_VERSION):
    log.append_claim(
        classifier_claim(attempt_id, ["sorting"], model=model, prompt_version=prompt_version)
    )


def test_a_claim_from_an_older_prompt_version_is_re_derived(backlog):
    machine_claim(backlog, "a1", prompt_version="0")

    result = run(answering(Verdict(["greedy"])), backlog, redo=True)

    standing = latest_by_attempt(backlog.claims())["a1"]
    assert standing.techniques == ["greedy"]
    assert (standing.model, standing.prompt_version) == (MODEL, PROMPT_VERSION)
    assert (result.redone, result.classified) == (1, 0)


def test_a_claim_from_another_model_is_re_derived(backlog):
    machine_claim(backlog, "a1", model="an-older-model")

    result = run(answering(Verdict(["greedy"])), backlog, redo=True)

    assert result.redone == 1


def test_a_claim_from_this_classifier_is_never_re_derived(backlog):
    """It would ask the same question of the same model and pay for the same
    answer."""
    machine_claim(backlog, "a1")
    client = answering()

    result = run(client, backlog, redo=True)

    assert (result.redone, client.messages.calls) == (0, [])


def test_a_stale_claim_is_left_alone_without_the_flag(backlog):
    """A re-derivation costs a call per attempt, so it is asked for."""
    machine_claim(backlog, "a1", prompt_version="0")
    client = answering()

    result = run(client, backlog)

    assert (result.redone, client.messages.calls) == (0, [])


def test_a_user_claim_is_never_stale(backlog):
    """Nothing re-derives it: it is what the classifier is corrected by."""
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

    result = run(client, backlog, redo=True)

    assert (result.redone, client.messages.calls) == (0, [])


def test_a_re_derivation_supersedes_rather_than_rewrites(backlog):
    """The log is append-only: the older claim stays in it and stops being
    read."""
    machine_claim(backlog, "a1", prompt_version="0")

    run(answering(Verdict(["greedy"])), backlog, redo=True)

    older, newer = backlog.claims()
    assert (older.prompt_version, older.techniques) == ("0", ["sorting"])
    assert (newer.prompt_version, newer.techniques) == (PROMPT_VERSION, ["greedy"])


def test_an_unchanged_verdict_is_still_written(backlog):
    """The record names the classifier that reached it, so an unwritten
    agreement would stay stale and be paid for on every later run."""
    machine_claim(backlog, "a1", prompt_version="0")

    run(answering(Verdict(["sorting"])), backlog, redo=True)
    result = run(answering(), backlog, redo=True)

    assert (len(backlog.claims()), result.redone) == (2, 0)


def test_unclaimed_attempts_are_claimed_before_stale_ones(tmp_path):
    """A first claim buys a number the board does not have; a re-derivation
    only revises one it does."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("unclaimed", "two-tags", finished_at=T0))
    log.append_attempt(attempt("stale", "two-tags", finished_at=T0 + timedelta(days=1)))
    machine_claim(log, "stale", prompt_version="0")

    run(answering(Verdict(["greedy"])), log, limit=1, redo=True)

    assert [claim.attempt_id for claim in log.claims()] == ["stale", "unclaimed"]


def test_naming_no_candidate_leaves_the_older_claim_standing(backlog):
    """A claim cannot say 'none of these', and the stale one answers the
    attempt until something replaces it."""
    machine_claim(backlog, "a1", prompt_version="0")

    result = run(answering(Verdict([])), backlog, redo=True)

    standing = latest_by_attempt(backlog.claims())["a1"]
    assert (standing.prompt_version, result.undecided, result.redone) == ("0", 1, 0)


def test_the_technique_flag_narrows_the_backlog(backlog):
    seed_problem(backlog.root, id="tries", tags=["Trie", "Sorting"])
    backlog.append_attempt(attempt("a3", "tries"))

    run(answering(Verdict(["trie"])), backlog, technique="trie")

    assert [claim.attempt_id for claim in backlog.claims()] == ["a3"]
