"""The gap report: the core templates the next generation run is aimed at."""

import pytest
from matching import canonical, card, problem, seeded, stored, template

from algo_coach import cli
from algo_coach.matches import MatchLog
from algo_coach.mint import generator_match
from algo_coach.solutions import SolutionLog


def run(monkeypatch, *argv: str) -> None:
    monkeypatch.setattr("sys.argv", ["algo-coach", "gaps", *argv])
    cli.main()


@pytest.fixture
def root(tmp_path, monkeypatch):
    """One card of two core forms, and a canonical displaying one of them."""
    data = tmp_path / "data"
    cards = seeded(data, card(templates=[template("fixed-window"), template("shrink-to-fit")]))
    stored(data, problem("p1", techniques=["sliding-window"]))
    solution = canonical("p1")
    SolutionLog(data).append(solution)
    fixed = next(one.id for one in cards[0].templates if one.slug == "fixed-window")
    MatchLog(data).append(generator_match(fixed, solution.id))
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    return data


def test_only_the_gaps_are_listed(root, monkeypatch, capsys):
    run(monkeypatch)

    out = capsys.readouterr().out
    assert "shrink-to-fit" in out
    assert "fixed-window" not in out
    assert "1 of 2 core template(s) carry no solution" in out


def test_every_core_template_under_all(root, monkeypatch, capsys):
    """What a form is covered by, since one solution is a thin rung."""
    run(monkeypatch, "--all")

    out = capsys.readouterr().out
    assert "fixed-window" in out
    assert "1 solution(s)" in out


def test_an_empty_store_reports_no_template(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")

    run(monkeypatch)

    assert "0 of 0 core template(s) carry no solution" in capsys.readouterr().out
