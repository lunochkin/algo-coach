from datetime import timedelta
from importlib import import_module

import pytest
from helpers import T0, FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import EFFORT, MODEL, request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim, user_claim
from algo_coach.schema import ClaimSource

CLIENT = import_module("algo_coach.cli.client")


def run(monkeypatch, client: FakeClient, *argv: str) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(CLIENT, "Anthropic", lambda: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "score", "--user", "u1", *argv])
    cli.main()


def reading(attempt_id: str, techniques: list[str], *, model: str = MODEL):
    return classifier_claim(
        attempt_id,
        techniques,
        model=model,
        effort=EFFORT,
        prompt_hash=request_hash(["greedy", "sorting"], "def f(): pass"),
        call_id="call-1",
    )


@pytest.fixture
def hand_claimed(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(user_claim("a1", ["greedy"]))
    return log


def test_the_command_reports_the_agreement(hand_claimed, monkeypatch, capsys):
    run(monkeypatch, FakeClient.answering(Verdict(["greedy"])))

    out = capsys.readouterr().out
    assert MODEL in out
    assert "1/1 exact (100%)" in out
    assert "greedy" in out


def test_the_rows_carry_what_was_over_claimed(hand_claimed, monkeypatch, capsys):
    run(monkeypatch, FakeClient.answering(Verdict(["greedy", "sorting"])))

    out = capsys.readouterr().out
    assert "0/1 exact (0%)" in out
    assert "sorting" in out


def test_the_disagreements_are_printed_in_full(hand_claimed, monkeypatch, capsys):
    """Reading them is how a mislabelled hand claim is caught, and a corrected
    claim supersedes the earlier one."""
    run(monkeypatch, FakeClient.answering(Verdict(["sorting"])))

    out = capsys.readouterr().out
    assert "a1" in out
    assert "you: greedy" in out
    assert "it:  sorting" in out


def test_the_command_says_what_it_paid_for(hand_claimed, monkeypatch, capsys):
    """A run is minutes of calls, and reuse is what the stored readings buy —
    so the cost is reported beside the share rather than inferred from it."""
    run(monkeypatch, FakeClient.answering(Verdict(["greedy"])))
    capsys.readouterr()

    run(monkeypatch, FakeClient.answering())

    out = capsys.readouterr().out
    assert "1 reused" in out


def test_the_command_says_how_many_named_no_candidate(hand_claimed, monkeypatch, capsys):
    """A classifier that declines gets a smaller denominator and a better share
    for it, so the declines are printed next to the share."""
    seed_problem(hand_claimed.root, id="second", tags=["Greedy", "Sorting"])
    hand_claimed.append_attempt(attempt("a2", "second", finished_at=T0 + timedelta(days=1)))
    hand_claimed.append_claim(user_claim("a2", ["greedy"]))

    run(monkeypatch, FakeClient.answering(Verdict([]), Verdict(["greedy"])))

    out = capsys.readouterr().out
    assert "1/1 exact (100%)" in out
    assert "1 named no candidate" in out


def test_the_named_classifier_is_the_one_scored(hand_claimed, monkeypatch, capsys):
    run(monkeypatch, FakeClient.answering(Verdict(["greedy"])), "--model", "a-cheap-model")

    out = capsys.readouterr().out
    assert "a-cheap-model" in out
    assert "1/1 exact (100%)" in out


def test_the_effort_attaches_to_the_model_before_it(hand_claimed, monkeypatch, capsys):
    """Two configurations of one model, told apart by what each was asked at —
    which is lost the moment the flags are collected separately."""
    run(
        monkeypatch,
        FakeClient.answering(Verdict(["greedy"]), Verdict(["sorting"])),
        *("--model", "a-model", "--effort", "low"),
        *("--model", "a-model", "--effort", "high"),
    )

    out = capsys.readouterr().out
    assert "a-model/low" in out
    assert "a-model/high" in out


def test_the_same_configuration_twice_is_refused(hand_claimed, monkeypatch, capsys):
    """It would measure the classifier's own sampling noise — a real number,
    and one nothing here consumes yet."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering(), "--model", "a-model", "--model", "a-model")

    assert exit_info.value.code == 2
    assert "named twice" in capsys.readouterr().err


def test_two_efforts_for_one_model_is_refused(hand_claimed, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering(), *("--effort", "low", "--effort", "high"))

    assert exit_info.value.code == 2
    assert "two --effort" in capsys.readouterr().err


def test_the_shares_are_over_what_both_read(hand_claimed, monkeypatch, capsys):
    """Two columns under one denominator: a cheaper classifier measured on its
    own smaller sample would read as the better one."""
    run(
        monkeypatch,
        FakeClient.answering(Verdict(["greedy"]), Verdict(["sorting"])),
        *("--model", MODEL, "--model", "a-cheap-model"),
    )

    out = capsys.readouterr().out
    assert "1 of 1 hand-claimed attempts read by all" in out
    assert "1/1 (100%)" in out
    assert "0/1 (0%)" in out
    # Named by model and effort both: effort moves a number as far as the model
    # does, so a column that dropped it would leave two readings under one name.
    assert f"{MODEL}/{EFFORT}: greedy" in out
    assert f"a-cheap-model/{EFFORT}: sorting" in out


def test_a_classifier_that_fails_every_call_aborts(hand_claimed, monkeypatch, capsys):
    """A model that rejects a parameter fails identically on every attempt —
    the eval set must not be paid for to learn it once."""
    seed_problem(hand_claimed.root, id="second", tags=["Greedy", "Sorting"])
    seed_problem(hand_claimed.root, id="third", tags=["Greedy", "Sorting"])
    for index, name in enumerate(("second", "third"), start=2):
        hand_claimed.append_attempt(
            attempt(f"a{index}", name, finished_at=T0 + timedelta(days=index))
        )
        hand_claimed.append_claim(user_claim(f"a{index}", ["greedy"]))
    rejected = Verdict(error=RuntimeError("does not support the effort parameter"))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering(rejected, rejected, rejected), "--model", "a-model")

    assert exit_info.value.code == 1
    assert "aborted after 3 consecutive failures" in capsys.readouterr().err


def test_an_unsupported_effort_can_be_left_unset(hand_claimed, monkeypatch, capsys):
    """`--effort default` is how a model that rejects the parameter is named:
    the level it ran at, stored like any other."""
    client = FakeClient.answering(Verdict(["greedy"]))

    run(monkeypatch, client, *("--effort", "default"))

    (call,) = client.messages.calls
    assert "effort" not in call["output_config"]
    (reading,) = [c for c in hand_claimed.claims() if c.source is ClaimSource.CLASSIFIER]
    assert reading.effort == "default"


def test_a_stored_run_makes_no_call_and_needs_no_key(hand_claimed, monkeypatch, capsys):
    """What makes it the reproducible mode: it can be run anywhere, and twice."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))
    for name in CLIENT.CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("sys.argv", ["algo-coach", "score", "--user", "u1", "--stored"])

    cli.main()

    assert "1/1 exact (100%)" in capsys.readouterr().out


def test_a_stored_run_with_a_limit_is_refused(hand_claimed, monkeypatch, capsys):
    """A cap on a run that pays for nothing states two different things."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering(), "--stored", "--limit", "5")

    assert exit_info.value.code == 2
    assert "--stored with --limit" in capsys.readouterr().err


def test_a_stored_run_over_nothing_read_exits_nonzero(hand_claimed, monkeypatch, capsys):
    """Ground truth exists and no reading of it does — told apart from having
    no ground truth at all, since only one of them is fixed by reading."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering(), "--stored")

    assert exit_info.value.code == 1
    assert "nothing every configuration named has read" in capsys.readouterr().err


def test_nothing_hand_claimed_exits_nonzero(tmp_path, monkeypatch, capsys):
    """No ground truth is not a score of zero — there is nothing to score."""
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-tags"))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeClient.answering())

    assert exit_info.value.code == 1
    assert "nothing hand-claimed" in capsys.readouterr().err
