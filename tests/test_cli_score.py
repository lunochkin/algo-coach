from datetime import timedelta
from importlib import import_module

import pytest
from helpers import T0, FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import MODEL
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim

CLIENT = import_module("algo_coach.cli.client")


def run(monkeypatch, client: FakeClient, *argv: str) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(CLIENT, "Anthropic", lambda: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "score", "--user", "u1", *argv])
    cli.main()


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
