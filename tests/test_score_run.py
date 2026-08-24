import json
import threading
import time
from datetime import timedelta

import pytest
from helpers import T0, FakeTransport, Verdict, attempt, machine_claim, seed_problem

from algo_coach.calls import CallLog, Reply
from algo_coach.claims import (
    DEFAULT,
    EFFORT,
    MODEL,
    PIN,
    Configuration,
    request_hash,
    score_backlog,
)
from algo_coach.claims.run import ABORT_AFTER
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import ClaimSource
from algo_coach.techniques import standing_claims

# What the one-attempt fixture would be sent now.
ASKED = request_hash(["greedy", "sorting"], "def f(): pass")


def reading(attempt_id: str, techniques: list[str], **configuration):
    """A stored reading at this classifier's configuration unless a test names
    the field it differs in."""
    return machine_claim(
        attempt_id,
        techniques,
        **{
            "model": MODEL,
            "effort": EFFORT,
            "prompt_hash": ASKED,
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


def compare(client, log, **kwargs):
    problems = {problem.id: problem for problem in ProblemStore(log.root).all()}
    return score_backlog(client, log, CallLog(log.root), problems, user_id="u1", **kwargs)


def run(client, log, **kwargs):
    """One configuration's score. A comparison of one is the same code path,
    so the tests that predate the flag read it unwrapped."""
    return compare(client, log, **kwargs).scores[0].score


def machine_claims(log):
    return [claim for claim in log.claims() if claim.source is ClaimSource.CLASSIFIER]


# A second classifier to put beside the built-in one. Cheaper only in the story
# the tests tell; what matters is that it is another configuration.
CHEAP = Configuration(model="a-cheap-model")


def test_agreement_is_scored_against_the_users_claim(hand_claimed):
    result = run(FakeTransport.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.scored, result.exact) == (1, 1)


def test_disagreement_is_scored_per_technique(hand_claimed):
    result = run(FakeTransport.answering(Verdict(["sorting"])), hand_claimed)

    rows = {row.technique: row for row in result.per_technique}
    assert (result.scored, result.exact) == (1, 0)
    assert (rows["greedy"].attempts, rows["greedy"].exact) == (1, 0)
    assert rows["sorting"].over == 1


def test_what_the_classifier_read_is_stored(hand_claimed):
    """An eval that forgot its verdicts would be evidence that exists only
    while it prints."""
    run(FakeTransport.answering(Verdict(["sorting"])), hand_claimed)

    (stored,) = machine_claims(hand_claimed)
    assert (stored.attempt_id, stored.techniques) == ("a1", ["sorting"])
    assert (stored.model, stored.effort, stored.prompt_hash) == (MODEL, EFFORT, ASKED)
    assert stored.call_id


def test_a_stored_reading_never_becomes_the_standing_claim(hand_claimed):
    """It is a reading, not a candidate: the user's claim wins by source, not
    by being the later record."""
    run(FakeTransport.answering(Verdict(["sorting"])), hand_claimed)

    standing = standing_claims(hand_claimed.claims())["a1"]
    assert [claim.techniques for claim in machine_claims(hand_claimed)] == [["sorting"]]
    assert (standing.source, standing.techniques) == (ClaimSource.USER, ["greedy"])


def test_a_second_run_at_this_configuration_pays_for_nothing(hand_claimed):
    """The same question of the same classifier has an answer in the log."""
    run(FakeTransport.answering(Verdict(["greedy"])), hand_claimed)
    client = FakeTransport.answering()

    result = run(client, hand_claimed)

    assert (result.scored, result.exact) == (1, 1)
    assert (result.read, result.reused, client.calls) == (0, 1, [])


def test_a_reading_stored_before_the_hand_claim_is_reused(tmp_path):
    """The ordinary correction path: the backlog run claims, the user corrects.
    Scoring that attempt is already paid for."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(reading("a1", ["sorting"]))
    log.append_claim(user_claim("a1", ["greedy"]))
    client = FakeTransport.answering()

    result = run(client, log)

    assert (result.scored, result.exact, result.reused) == (1, 0, 1)
    assert client.calls == []


def test_a_rolled_back_rulebook_reuses_the_reading_under_it(hand_claimed):
    """Running an earlier rulebook on purpose is a rollback, so the reading
    answering today's question can sit under a later one and still answer."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))
    hand_claimed.append_claim(reading("a1", ["sorting"], prompt_hash="ffffffffffff"))
    client = FakeTransport.answering()

    result = run(client, hand_claimed)

    assert (result.exact, result.reused, client.calls) == (1, 1, [])


def test_a_reading_answering_another_prompt_is_read_again(hand_claimed):
    hand_claimed.append_claim(reading("a1", ["sorting"], prompt_hash="ffffffffffff"))

    result = run(FakeTransport.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.read, result.reused, result.exact) == (1, 0, 1)


def test_a_reading_from_another_model_is_read_again(hand_claimed):
    hand_claimed.append_claim(reading("a1", ["sorting"], model="an-older-model"))

    result = run(FakeTransport.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.read, result.exact) == (1, 1)


def test_a_reading_answering_the_same_prompt_is_reused(hand_claimed):
    """The saving: an edit this attempt's candidates never carried leaves its
    stored reading answering the same question, and nothing is paid twice."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))
    client = FakeTransport.answering()

    result = run(client, hand_claimed)

    assert (result.reused, client.calls) == (1, [])


def test_fresh_asks_again_where_a_reading_already_answers(hand_claimed):
    """A run measuring a model against itself needs the same question asked
    twice, which is the one thing a cache exists to prevent."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))

    result = run(FakeTransport.answering(Verdict(["sorting"])), hand_claimed, fresh=True)

    assert (result.read, result.reused) == (1, 0)


def test_naming_no_candidate_is_scored_against_a_claim_that_named_some(hand_claimed):
    """It asserts that none of the candidates apply, which a claim naming one
    of them contradicts. Counted apart as well, since a decline is worth
    seeing — but not excused from the score for being one."""
    result = run(FakeTransport.answering(Verdict([])), hand_claimed)

    (reading,) = machine_claims(hand_claimed)
    assert (result.scored, result.exact, result.undecided) == (1, 0, 1)
    assert reading.techniques == []
    # Missed against every technique the claim named, and over-claimed on none.
    (row,) = [one for one in result.per_technique if one.technique == "greedy"]
    assert (row.attempts, row.missed, row.over) == (1, 1, 0)


def test_a_reading_that_named_no_candidate_is_paid_for_once(hand_claimed):
    """The decline is stored, so a later run reads it back rather than asking
    again. The answer does not change while the question does not."""
    run(FakeTransport.answering(Verdict([])), hand_claimed)
    client = FakeTransport.answering(Verdict([]))

    result = run(client, hand_claimed)

    assert (result.undecided, result.scored, len(client.calls)) == (1, 1, 0)


def test_a_failed_reading_stores_nothing(hand_claimed):
    result = run(FakeTransport.answering(Verdict(error=RuntimeError("refused"))), hand_claimed)

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

    client = FakeTransport.answering()
    result = run(client, log)

    assert (result.scored, client.calls) == (0, [])


def test_an_unclaimed_attempt_is_not_scored(tmp_path):
    """Nothing to score it against — the hand pass has not reached it."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))

    client = FakeTransport.answering()

    assert (run(client, log).scored, client.calls) == (0, [])


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

    result = run(FakeTransport.answering(Verdict(["sorting"])), log)

    assert (result.scored, result.exact, result.failed) == (1, 1, [])


def test_one_failure_does_not_cost_the_rest(two_problems):
    """An eval that dies on the first refusal reports nothing about the rest."""
    result = run(
        FakeTransport.answering(Verdict(error=RuntimeError("refused")), Verdict(["greedy"])),
        two_problems,
    )

    assert (result.scored, result.exact) == (1, 1)
    assert [failure.attempt_id for failure in result.failed] == ["a2"]


def test_the_limit_caps_the_calls_not_the_score(two_problems):
    """A stored reading is free, so a capped run adds to what earlier runs read
    rather than reporting on a slice of it."""
    two_problems.append_claim(reading("a2", ["greedy"]))
    client = FakeTransport.answering(Verdict(["greedy"]))

    result = run(client, two_problems, limit=1)

    assert (result.scored, result.exact) == (2, 2)
    assert (result.read, result.reused, len(client.calls)) == (1, 1, 1)


def test_a_run_of_failures_aborts_rather_than_paying_for_the_eval_set(tmp_path):
    """A configuration this classifier cannot run fails identically on every
    attempt, and the eval set is the wrong place to learn that once."""
    root = tmp_path / "data"
    log = AttemptLog(root)
    for index in range(ABORT_AFTER + 2):
        seed_problem(root, id=f"p{index}", tags=["Greedy", "Sorting"])
        log.append_attempt(attempt(f"a{index}", f"p{index}", finished_at=T0))
        log.append_claim(user_claim(f"a{index}", ["greedy"]))
    broken = Verdict(error=RuntimeError("does not support the effort parameter"))
    client = FakeTransport.answering(*[broken] * (ABORT_AFTER + 2))

    result = compare(client, log, configurations=(CHEAP,))

    assert result.scores[0].score.aborted
    assert len(client.calls) == ABORT_AFTER


def test_a_scattered_failure_does_not_abort(two_problems):
    """One refusal is one attempt's problem — an eval that stopped there would
    report nothing about the attempts behind it."""
    client = FakeTransport.answering(Verdict(error=RuntimeError("refused")), Verdict(["greedy"]))

    result = compare(client, two_problems)

    assert not result.scores[0].score.aborted
    assert result.scores[0].score.scored == 1


def test_a_named_configuration_stores_its_own_provenance(hand_claimed):
    """A reading names the classifier that reached it, or a later run could not
    tell whose answer it was reusing."""
    run(FakeTransport.answering(Verdict(["greedy"])), hand_claimed, configurations=(CHEAP,))

    (stored,) = machine_claims(hand_claimed)
    assert (stored.model, stored.effort) == (CHEAP.model, CHEAP.effort)
    # What this attempt was actually sent, which no caller selects.
    assert stored.prompt_hash == ASKED


def test_the_shares_are_over_the_attempts_every_configuration_read(two_problems):
    """A configuration measured on a smaller sample scores against a different
    denominator, and the number would read as quality."""
    two_problems.append_claim(reading("a1", ["greedy"]))
    two_problems.append_claim(reading("a2", ["greedy"]))
    # The cheap one reads the newest and stops there, so a1 is the built-in
    # classifier's alone and belongs to neither share. Scripted by model: the
    # built-in one reuses both readings and asks nothing, so a script naming it
    # would say a call was expected that never comes.
    client = FakeTransport.per_deployment({(CHEAP.model, CHEAP.pin): Verdict(["sorting"])})

    result = compare(client, two_problems, configurations=(DEFAULT, CHEAP), limit=1)

    assert (result.eval_set, result.common) == (2, 1)
    assert [scored.score.scored for scored in result.scores] == [1, 1]
    assert [scored.score.exact for scored in result.scores] == [1, 0]


def test_the_limit_caps_the_calls_of_each_configuration(two_problems):
    """A cap across the run would spend it all on the first classifier and
    measure the second on nothing."""
    client = FakeTransport.per_deployment(
        {(MODEL, PIN): Verdict(["greedy"]), (CHEAP.model, CHEAP.pin): Verdict(["greedy"])}
    )

    result = compare(client, two_problems, configurations=(DEFAULT, CHEAP), limit=1)

    assert [scored.score.read for scored in result.scores] == [1, 1]
    # How many calls, not which came first: with the configurations running at
    # once the order they arrive in is not a fact about the cap.
    assert (len(client.calls), result.common) == (2, 1)
    assert client.asked("model") == {MODEL, CHEAP.model}


def test_an_attempt_one_configuration_declined_stays_in_both_denominators(two_problems):
    """A decline is an answer, so it keeps the attempt in `common`. Dropping it
    would shrink the denominator for every configuration whenever any one of
    them declined — and reward the one that did."""
    two_problems.append_claim(reading("a1", ["greedy"]))
    two_problems.append_claim(reading("a2", ["greedy"]))
    # Only the cheap one asks; the newest attempt is what it declines.
    client = FakeTransport.per_deployment(
        {(CHEAP.model, CHEAP.pin): [Verdict([]), Verdict(["greedy"])]}
    )

    result = compare(client, two_problems, configurations=(DEFAULT, CHEAP))

    assert result.common == 2
    assert [scored.score.scored for scored in result.scores] == [2, 2]
    assert result.scores[1].score.undecided == 1
    # The decline is the one it got wrong.
    assert [scored.score.exact for scored in result.scores] == [2, 1]


def test_only_the_attempts_they_answered_differently_are_split(two_problems):
    """Where they agreed there is nothing to choose between them, however wrong
    both are — a1 is where reading the code decides which to keep."""
    two_problems.append_claim(reading("a1", ["sorting"]))
    two_problems.append_claim(reading("a2", ["sorting"]))
    client = FakeTransport.per_deployment(
        {(CHEAP.model, CHEAP.pin): [Verdict(["sorting"]), Verdict(["greedy"])]}
    )

    result = compare(client, two_problems, configurations=(DEFAULT, CHEAP))

    assert [split.attempt_id for split in result.splits] == ["a1"]
    assert result.splits[0].verdicts == [["sorting"], ["greedy"]]
    assert result.splits[0].user == ["greedy"]


def test_one_configuration_is_compared_with_nothing(hand_claimed):
    """The comparison of one is the ordinary score, so nothing splits and the
    denominator is what that configuration read."""
    result = compare(FakeTransport.answering(Verdict(["greedy"])), hand_claimed)

    assert (result.common, result.splits) == (1, [])
    assert result.scores[0].configuration == DEFAULT


def test_a_cap_of_no_calls_scores_what_is_already_stored(hand_claimed):
    """The reproducible run: nothing is paid for, so the client is never
    reached and need not exist."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))

    result = compare(None, hand_claimed, limit=0)

    assert (result.common, result.scores[0].score.reused) == (1, 1)


# Two configurations of one model on one endpoint: the same deployment answers
# both, so they share whatever meters it.
LOW = Configuration(effort="low")
HIGH = Configuration(effort="high")


class Counting:
    """A transport that reports how many of its calls overlapped, and where."""

    def __init__(self, hold: float = 0.005):
        self.hold = hold
        self.lock = threading.Lock()
        self.live: dict[tuple[str, str], int] = {}
        self.peak: dict[tuple[str, str], int] = {}
        self.calls = 0

    def __call__(self, **kwargs):
        key = (kwargs["model"], kwargs["pin"])
        with self.lock:
            self.calls += 1
            self.live[key] = self.live.get(key, 0) + 1
            self.peak[key] = max(self.peak.get(key, 0), self.live[key])
        time.sleep(self.hold)
        with self.lock:
            self.live[key] -= 1
        return Reply(text=json.dumps({"techniques": ["greedy"]}), stop_reason="stop")


def spread(root, count: int) -> AttemptLog:
    """A hand claim on each of `count` problems, so a run has that many calls
    to spend per configuration."""
    log = AttemptLog(root)
    for index in range(count):
        seed_problem(root, id=f"p{index}", tags=["Greedy", "Sorting"])
        log.append_attempt(
            attempt(f"a{index}", f"p{index}", finished_at=T0 + timedelta(days=index))
        )
        log.append_claim(user_claim(f"a{index}", ["greedy"]))
    return log


def test_configurations_on_one_deployment_share_a_budget(tmp_path):
    """Effort does not change which deployment answers, so two efforts of one
    model are one endpoint's traffic and one endpoint's cap."""
    client = Counting()

    compare(client, spread(tmp_path / "data", 6), configurations=(LOW, HIGH), concurrency=1)

    assert client.peak == {(LOW.model, LOW.pin): 1}
    assert client.calls == 12


def test_configurations_on_different_deployments_run_at_once(tmp_path):
    """The whole change: one budget each, spent together. The barrier clears
    only if both deployments have a call in flight."""
    ready = threading.Barrier(2, timeout=5)
    other = Configuration(model="b-model", pin="b-host")

    def client(**kwargs):
        ready.wait()
        return Reply(text=json.dumps({"techniques": ["greedy"]}), stop_reason="stop")

    result = compare(
        client, spread(tmp_path / "data", 2), configurations=(DEFAULT, other), concurrency=1
    )

    assert [scored.score.read for scored in result.scores] == [2, 2]


def test_one_configuration_aborting_leaves_the_others_reading(tmp_path):
    """A broken model is not a broken endpoint. The plan stops being drawn
    from; the deployment it shares keeps answering."""
    broken = RuntimeError("does not support the effort parameter")

    # Keyed on the effort, which is what separates these two — the deployment
    # cannot, since sharing one is the whole point of the case.
    def client(**kwargs):
        if kwargs["effort"] == LOW.effort:
            raise broken
        return Reply(text=json.dumps({"techniques": ["greedy"]}), stop_reason="stop")

    result = compare(client, spread(tmp_path / "data", ABORT_AFTER + 2), configurations=(LOW, HIGH))

    assert result.scores[0].score.aborted
    assert len(result.scores[0].score.failed) == ABORT_AFTER
    assert not result.scores[1].score.aborted
    assert result.scores[1].score.read == ABORT_AFTER + 2


def test_the_log_has_one_writer_however_many_configurations_run(tmp_path, monkeypatch):
    """Claims are appended as they are read, and an append-only file cannot be
    written by two threads at once. Every write is the consuming thread's."""
    log = spread(tmp_path / "data", 6)
    writers = []
    appended = log.append_claim

    def watched(claim):
        writers.append(threading.current_thread())
        appended(claim)

    monkeypatch.setattr(log, "append_claim", watched)
    other = Configuration(model="b-model", pin="b-host")

    compare(Counting(), log, configurations=(DEFAULT, other), concurrency=3)

    assert writers
    assert set(writers) == {threading.current_thread()}


def test_every_configuration_is_planned_before_the_first_call(tmp_path):
    """A reader needs every total up front, and one answered entirely from the
    log asks for nothing — reported as it started, it would never appear."""
    log = spread(tmp_path / "data", 2)
    log.append_claim(reading("a0", ["greedy"]))
    log.append_claim(reading("a1", ["greedy"]))
    planned = []

    compare(
        FakeTransport.per_deployment({(CHEAP.model, CHEAP.pin): Verdict(["greedy"])}),
        log,
        configurations=(DEFAULT, CHEAP),
        on_plan=planned.append,
    )

    (plans,) = planned
    assert [len(plan.asking) for plan in plans] == [0, 2]
    assert [plan.configuration for plan in plans] == [DEFAULT, CHEAP]


def test_a_progress_report_names_the_configuration_that_read_it(tmp_path):
    """Several answer at once, so a line that did not say whose it was could
    not be attributed at all."""
    seen = []

    compare(
        Counting(),
        spread(tmp_path / "data", 2),
        configurations=(LOW, HIGH),
        on_progress=lambda configuration, progress: seen.append((configuration, progress.index)),
    )

    assert {configuration for configuration, _ in seen} == {LOW, HIGH}
    assert sorted(index for _, index in seen) == [1, 1, 2, 2]


def test_a_reading_carries_what_it_was_charged(hand_claimed):
    """Recorded rather than derived: a price moves, so a rate applied later
    says what a reading would cost now instead of what it cost."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    client.cost = 0.0042

    result = run(client, hand_claimed)

    assert (result.cost, result.costed) == (0.0042, 1)
    (stored,) = machine_claims(hand_claimed)
    assert stored.cost == 0.0042


def test_a_reused_reading_brings_its_own_price(hand_claimed):
    """The run that paid it recorded it. Re-reading the log must not make an
    old reading look free, nor reprice it at today's rate."""
    hand_claimed.append_claim(reading("a1", ["greedy"], cost=0.0031))

    result = run(None, hand_claimed, limit=0)

    assert (result.reused, result.costed) == (1, 1)
    assert result.cost == 0.0031


def test_a_reading_stored_before_the_price_is_left_out_of_the_mean(hand_claimed):
    """Counting it as free would flatter whichever configuration was read
    earliest, which is the opposite of what the column is for."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))

    result = run(None, hand_claimed, limit=0)

    assert (result.reused, result.costed, result.cost) == (1, 0, 0.0)


def test_what_a_reading_consumed_is_joined_from_its_call(hand_claimed):
    """A claim deliberately holds no token counts, so the report reads them
    from the call it cites rather than from a copy that could drift."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    client.tokens = (1100, 400, 380)

    result = run(client, hand_claimed)

    assert (result.input_tokens, result.output_tokens) == (1100, 400)
    assert (result.reasoning_tokens, result.tokened, result.reasoned) == (380, 1, 1)


def test_a_call_reporting_no_thinking_split_is_counted_apart(hand_claimed):
    """A model that reports the total and not the part spent reasoning is not
    a model that reasoned nothing, so the two have separate denominators."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    client.tokens = (1100, 400, None)

    result = run(client, hand_claimed)

    assert (result.tokened, result.reasoned) == (1, 0)
    assert result.output_tokens == 400


def test_a_reused_reading_brings_its_calls_counts_too(hand_claimed):
    """The join is by call id, so a reading paid for by an earlier run counts
    the same as one this run made."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    client.tokens = (900, 200, 150)
    run(client, hand_claimed)

    again = run(None, hand_claimed, limit=0)

    assert (again.reused, again.tokened) == (1, 1)
    assert (again.input_tokens, again.reasoning_tokens) == (900, 150)


def test_the_timing_is_the_request_not_the_wait(hand_claimed):
    """A run held behind a cap waited longer than the model took. The
    difference is the endpoint's backoff, and counting it would read as a slow
    reader."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    client.request_ms = 14000

    result = run(client, hand_claimed)

    assert (result.request_ms, result.slowest_ms, result.timed) == (14000, 14000, 1)


def test_the_slowest_request_is_kept_beside_the_mean(two_problems):
    """A reader that stalls on one attempt in eighty is a different problem
    from one that is uniformly slow, and a mean cannot tell them apart."""
    client = FakeTransport.answering(Verdict(["greedy"]), Verdict(["greedy"]))
    client.request_ms = [2000, 30000]

    result = run(client, two_problems)

    assert result.timed == 2
    assert result.slowest_ms == 30000
    assert result.request_ms == 32000
