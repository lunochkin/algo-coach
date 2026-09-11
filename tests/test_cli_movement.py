import pytest
from commands import connected, run_cli
from helpers import attempt, logged, machine_claim, seed_problem

from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim


def run(monkeypatch, *argv: str) -> None:
    run_cli(monkeypatch, "movement", "--user", "u1", *argv)


@pytest.fixture
def classified(database, monkeypatch) -> AttemptLog:
    data = connected(database, monkeypatch)
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-codes"))
    logged(log, machine_claim("a1", ["greedy"]))
    return log


def test_the_command_reports_what_the_claims_took_away(classified, monkeypatch, capsys):
    run(monkeypatch)

    out = capsys.readouterr().out
    assert "sorting" in out
    assert "-1" in out
    assert "1 classifier claim(s)" in out


def test_a_hand_claim_is_not_the_classifier_s_movement(database, monkeypatch, capsys):
    """A user claim narrows for a different reason; crediting the machine with
    it would read as a classifier that decided something."""
    data = connected(database, monkeypatch)
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-codes"))
    logged(log, user_claim("a1", ["greedy"]))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch)

    assert exit_info.value.code == 1
    assert "nothing classified" in capsys.readouterr().err


def test_nothing_classified_exits_nonzero(database, monkeypatch, capsys):
    data = connected(database, monkeypatch)
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    AttemptLog(data).append_attempt(attempt("a1", "two-codes"))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch)

    assert exit_info.value.code == 1
