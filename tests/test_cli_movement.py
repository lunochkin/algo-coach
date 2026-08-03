import pytest
from helpers import attempt, seed_problem

from algo_coach import cli
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim, user_claim


def run(monkeypatch, *argv: str) -> None:
    monkeypatch.setattr("sys.argv", ["algo-coach", "movement", "--user", "u1", *argv])
    cli.main()


@pytest.fixture
def classified(tmp_path, monkeypatch) -> AttemptLog:
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(classifier_claim("a1", ["greedy"], model="a-model", prompt_version="1"))
    return log


def test_the_command_reports_what_the_claims_took_away(classified, monkeypatch, capsys):
    run(monkeypatch)

    out = capsys.readouterr().out
    assert "sorting" in out
    assert "-1" in out
    assert "1 classifier claim(s)" in out


def test_a_hand_claim_is_not_the_classifier_s_movement(tmp_path, monkeypatch, capsys):
    """A hand claim narrows for a different reason; crediting the machine with
    it would read as a classifier that decided something."""
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_claim(user_claim("a1", ["greedy"]))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch)

    assert exit_info.value.code == 1
    assert "nothing classified" in capsys.readouterr().err


def test_nothing_classified_exits_nonzero(tmp_path, monkeypatch, capsys):
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-tags"))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch)

    assert exit_info.value.code == 1
