import threading
from datetime import timedelta

import pytest
from helpers import T0, FakeTransport, Verdict, attempt, machine_claim, seed_problem

from algo_coach import cli
from algo_coach.calls import CallLog
from algo_coach.claims import classify_backlog
from algo_coach.claims.run import ABORT_AFTER, Progress
from algo_coach.classifier import EFFORT, MODEL, ClassifierError, Configuration, request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import ClaimSource, TechniqueClaim
from algo_coach.techniques import standing_claims

answering = FakeTransport.answering


@pytest.fixture
def backlog(tmp_path, monkeypatch) -> AttemptLog:
    """One two-tag problem and one single-tag problem, an attempt on each."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    seed_problem(root, id="one-tag", techniques=["trie"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-codes"))
    log.append_attempt(attempt("a2", "one-tag"))
    return log


def stored(log: AttemptLog):
    return {problem.id: problem for problem in ProblemStore(log.root).all()}


def run(client, log, **kwargs):
    return classify_backlog(client, log, CallLog(log.root), stored(log), user_id="u1", **kwargs)


def test_a_verdict_is_written_as_a_classifier_claim(backlog):
    client = answering(Verdict(["greedy"]))

    result = run(client, backlog)

    (claim,) = backlog.claims()
    assert claim.attempt_id == "a1"
    assert claim.techniques == ["greedy"]
    assert claim.source is ClaimSource.CLASSIFIER
    assert (claim.model, claim.prompt_hash) == (MODEL, ASKED)
    assert result.classified == 1


def test_a_single_tag_problem_is_never_asked_about(backlog):
    """Its fallback already answers; a claim there disputes nothing, and it
    would cost a call to agree with the tags."""
    client = answering(Verdict(["greedy"]))

    run(client, backlog)

    assert [claim.attempt_id for claim in backlog.claims()] == ["a1"]
    assert len(client.calls) == 1


def test_an_attempt_without_code_is_never_asked_about(tmp_path, monkeypatch):
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-codes", code=None))

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

    assert (result.classified, client.calls) == (0, [])


def test_a_run_resumes_where_the_last_one_stopped(tmp_path, monkeypatch):
    """Claims land as they are made and a claimed attempt drops out, so the
    backlog is not paid for twice."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-codes", finished_at=T0))
    log.append_attempt(attempt("a2", "two-codes", finished_at=T0 + timedelta(days=1)))

    run(answering(Verdict(["greedy"])), log, limit=1)
    run(answering(Verdict(["sorting"])), log, limit=1)

    assert sorted(claim.attempt_id for claim in log.claims()) == ["a1", "a2"]


def test_the_newest_attempts_are_claimed_first(tmp_path, monkeypatch):
    """A run cut short by `limit` improves the numbers the board is showing."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("old", "two-codes", finished_at=T0))
    log.append_attempt(attempt("new", "two-codes", finished_at=T0 + timedelta(days=1)))

    run(answering(Verdict(["greedy"])), log, limit=1)

    assert [claim.attempt_id for claim in log.claims()] == ["new"]


def test_naming_no_candidate_is_stored_and_answers_nothing(backlog):
    """The classifier read the code and found the candidates did not cover it.
    Kept, so no later run pays for the same answer; counted apart from a
    claim, since it names nothing the board can group by."""
    result = run(answering(Verdict([])), backlog)

    (claim,) = backlog.claims()
    assert (result.classified, result.undecided) == (0, 1)
    assert claim.techniques == []


def test_a_stored_decline_is_not_asked_again(backlog):
    """What it costs to store one: the run after it makes no call at all."""
    run(answering(Verdict([])), backlog)
    client = answering(Verdict(["greedy"]))

    result = run(client, backlog)

    assert (result.classified, len(client.calls)) == (0, 0)


def test_one_failure_does_not_cost_the_attempts_behind_it(tmp_path, monkeypatch):
    """A refusal, a rate limit or a dropped connection is one attempt's
    problem; a backlog run must not lose the rest."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-codes", finished_at=T0))
    log.append_attempt(attempt("a2", "two-codes", finished_at=T0 + timedelta(days=1)))

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
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    for age in reversed(range(count)):
        log.append_attempt(attempt(f"a{age}", "two-codes", finished_at=T0 + timedelta(days=-age)))
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
    assert len(client.calls) == ABORT_AFTER
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
    assert len(client.calls) == ABORT_AFTER * 2


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


def test_progress_is_reported_per_attempt_as_the_run_goes(tmp_path):
    """A call takes seconds, so the count at the end is not the report — the
    caller hears about each attempt when it is answered."""
    log = backlog_of(tmp_path / "data", 3)
    seen: list[Progress] = []

    run(answering(Verdict(["greedy"]), Verdict([]), broken()), log, on_progress=seen.append)

    assert [(p.index, p.total) for p in seen] == [(1, 3), (2, 3), (3, 3)]
    assert seen[0].techniques == ["greedy"]
    assert (seen[1].techniques, seen[1].reason) == ([], None)  # undecided
    assert "bad key" in seen[2].reason
    assert {p.title for p in seen} == {"two-codes"}


def test_progress_counts_only_what_the_run_asks_about(backlog):
    """A single-tag problem is never asked about, so it is not in the total —
    a denominator the run never reaches would stall at the last line."""
    seen: list[Progress] = []

    run(answering(Verdict(["greedy"])), backlog, on_progress=seen.append)

    assert [(p.index, p.total) for p in seen] == [(1, 1)]


# What the two-tag fixture attempt would be sent now. A claim carrying it is
# answering the question this run would ask; anything else is stale.
ASKED = request_hash(["greedy", "sorting"], "def f(): pass")


def store_claim(log, attempt_id, **configuration):
    """A stored machine claim at this classifier's configuration unless a test
    names the field it differs in."""
    log.append_claim(
        machine_claim(
            attempt_id,
            ["sorting"],
            **{"model": MODEL, "effort": EFFORT, "prompt_hash": ASKED} | configuration,
        )
    )


def test_a_claim_answering_another_prompt_is_re_derived(backlog):
    """The rulebook moved for this attempt, so the reading is worth paying for
    again — and only for the attempts the edit reached."""
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")

    result = run(answering(Verdict(["greedy"])), backlog, redo=True)

    standing = standing_claims(backlog.claims())["a1"]
    assert standing.techniques == ["greedy"]
    assert (standing.model, standing.effort, standing.prompt_hash) == (MODEL, EFFORT, ASKED)
    assert (result.redone, result.classified) == (1, 0)


def test_a_claim_from_another_model_is_re_derived(backlog):
    store_claim(backlog, "a1", model="an-older-model")

    result = run(answering(Verdict(["greedy"])), backlog, redo=True)

    assert result.redone == 1


def test_a_claim_from_another_effort_is_re_derived(backlog):
    """How hard the model was asked to think decides the reading, so it is a
    configuration of its own rather than something folded into the version."""
    store_claim(backlog, "a1", effort="low")

    result = run(answering(Verdict(["greedy"])), backlog, redo=True)

    assert result.redone == 1


def test_an_edit_the_prompt_never_reached_costs_nothing(backlog):
    """The saving the whole scheme is for: a criterion travels with its
    candidate, so editing an entry this attempt never sees leaves its stored
    reading answering the same question, and the run makes no call."""
    store_claim(backlog, "a1")
    client = answering()

    result = run(client, backlog, redo=True)

    assert (result.redone, client.calls) == (0, [])


def test_a_claim_from_this_classifier_is_never_re_derived(backlog):
    """It would ask the same question of the same model and pay for the same
    answer."""
    store_claim(backlog, "a1")
    client = answering()

    result = run(client, backlog, redo=True)

    assert (result.redone, client.calls) == (0, [])


def test_a_stale_claim_is_left_alone_without_the_flag(backlog):
    """A re-derivation costs a call per attempt, so it is asked for."""
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")
    client = answering()

    result = run(client, backlog)

    assert (result.redone, client.calls) == (0, [])


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

    assert (result.redone, client.calls) == (0, [])


def test_a_reading_stored_under_a_hand_claim_is_never_re_derived(backlog):
    """The eval stores what it read on hand-claimed attempts. It holds at this
    configuration and at any other: the user's claim is what stands there, and
    nothing re-derives it — so the reading under it is never asked again."""
    backlog.append_claim(user_claim("a1", ["greedy"]))
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")
    client = answering()

    result = run(client, backlog, redo=True)

    assert (result.redone, result.classified, client.calls) == (0, 0, [])


def test_a_re_derivation_supersedes_rather_than_rewrites(backlog):
    """The log is append-only: the older claim stays in it and stops being
    read."""
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")

    run(answering(Verdict(["greedy"])), backlog, redo=True)

    older, newer = backlog.claims()
    assert (older.prompt_hash, older.techniques) == ("ffffffffffff", ["sorting"])
    assert (newer.prompt_hash, newer.techniques) == (ASKED, ["greedy"])


def test_an_unchanged_verdict_is_still_written(backlog):
    """The record names the classifier that reached it, so an unwritten
    agreement would stay stale and be paid for on every later run."""
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")

    run(answering(Verdict(["sorting"])), backlog, redo=True)
    result = run(answering(), backlog, redo=True)

    assert (len(backlog.claims()), result.redone) == (2, 0)


def test_unclaimed_attempts_are_claimed_before_stale_ones(tmp_path):
    """A first claim buys a number the board does not have; a re-derivation
    only revises one it does."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("unclaimed", "two-codes", finished_at=T0))
    log.append_attempt(attempt("stale", "two-codes", finished_at=T0 + timedelta(days=1)))
    store_claim(log, "stale", prompt_hash="ffffffffffff")

    run(answering(Verdict(["greedy"])), log, limit=1, redo=True)

    assert [claim.attempt_id for claim in log.claims()] == ["stale", "unclaimed"]


def test_naming_no_candidate_supersedes_the_older_claim(backlog):
    """Latest wins, as everywhere else in the log: a later reading saying the
    candidates do not cover the code is evidence about the code, not an
    absence of it. The board falls back to the tags rather than to a claim
    made against a rulebook this reading disagrees with."""
    store_claim(backlog, "a1", prompt_hash="ffffffffffff")

    result = run(answering(Verdict([])), backlog, redo=True)

    standing = standing_claims(backlog.claims())["a1"]
    assert (standing.techniques, result.undecided, result.redone) == ([], 1, 0)


def test_the_technique_flag_narrows_the_backlog(backlog):
    seed_problem(backlog.root, id="tries", techniques=["sorting", "trie"])
    backlog.append_attempt(attempt("a3", "tries"))

    run(answering(Verdict(["trie"])), backlog, technique="trie")

    assert [claim.attempt_id for claim in backlog.claims()] == ["a3"]


def test_the_log_has_one_writer_however_many_calls_are_in_flight(tmp_path):
    """A torn line in an append-only log cannot be taken back, so the calls fan
    out and the write stays on the thread that drives the run."""
    log = backlog_of(tmp_path / "data", 6)
    appending = log.append_claim
    writers: list[threading.Thread] = []

    def watched(claim):
        writers.append(threading.current_thread())
        appending(claim)

    log.append_claim = watched
    client = answering(*[Verdict(["greedy"])] * 6)

    result = run(client, log, concurrency=4)

    assert result.classified == 6
    assert set(writers) == {threading.current_thread()}


def test_a_concurrent_run_claims_every_attempt_once(tmp_path):
    """Completion order is not the order asked in, and a verdict must still
    land on the attempt it was read from."""
    log = backlog_of(tmp_path / "data", 8)
    client = answering(*[Verdict(["greedy"])] * 8)

    result = run(client, log, concurrency=4)

    claimed = [claim.attempt_id for claim in log.claims()]
    assert result.classified == 8
    assert sorted(claimed) == sorted(f"a{age}" for age in range(8))


def test_a_concurrent_run_counts_up_as_answers_arrive(tmp_path):
    """A position in the order asked would jump about with calls in flight;
    what a reader wants is a count that climbs."""
    log = backlog_of(tmp_path / "data", 6)
    client = answering(*[Verdict(["greedy"])] * 6)
    seen: list[Progress] = []

    run(client, log, concurrency=3, on_progress=seen.append)

    assert [progress.index for progress in seen] == [1, 2, 3, 4, 5, 6]
    assert {progress.total for progress in seen} == {6}


def test_a_call_is_recorded_beside_the_claim_it_produced(tmp_path):
    """The claim says what stands; the call says what happened, and carries
    what a claim structurally cannot — the tokens and the reasoning."""
    log = backlog_of(tmp_path / "data", 1)
    calls = CallLog(log.root)

    classify_backlog(answering(Verdict(["greedy"])), log, calls, stored(log), user_id="u1")

    (claim,) = log.claims()
    (call,) = calls.all()
    assert claim.call_id == call.id
    assert (claim.model, claim.prompt_hash) == (call.model, call.prompt_hash)


def test_a_declined_verdict_is_a_call_and_a_claim_naming_nothing(tmp_path):
    """Both logs hold it: the call says what it cost, the claim says the
    question is answered and needs no second call."""
    log = backlog_of(tmp_path / "data", 1)
    calls = CallLog(log.root)

    result = classify_backlog(answering(Verdict([])), log, calls, stored(log), user_id="u1")

    (claim,) = log.claims()
    assert (result.undecided, claim.techniques) == (1, [])
    assert len(calls.all()) == 1


def test_a_failed_call_is_recorded_though_nothing_claims_it(tmp_path):
    log = backlog_of(tmp_path / "data", 1)
    calls = CallLog(log.root)

    result = classify_backlog(answering(broken()), log, calls, stored(log), user_id="u1")

    assert (len(result.failed), log.claims()) == (1, [])
    (call,) = calls.all()
    assert call.error and call.response is None


def test_fresh_asks_again_where_a_claim_already_answers(tmp_path):
    """Which a cache exists to prevent — so a run measuring a model against
    itself has to say it wants the question asked twice."""
    log = backlog_of(tmp_path / "data", 1)
    store_claim(log, "a0")

    result = run(answering(Verdict(["greedy"])), log, redo=True, fresh=True)

    assert result.redone == 1


def test_the_claim_carries_what_the_reading_was_sampled_at(backlog):
    """Copied from the call in the same write, so the claims file names the
    whole configuration without opening the call log — a board renders from it,
    and loading the calls to learn how a claim was produced would put a
    megabyte-scale read on every command."""
    run(
        backlog_client := answering(Verdict(["greedy"])),
        backlog,
        configuration=Configuration(model="a-model", effort="low", temperature=0.0),
    )

    (claim,) = backlog.claims()
    assert claim.temperature == 0.0
    assert backlog_client.calls[0]["temperature"] == 0.0
