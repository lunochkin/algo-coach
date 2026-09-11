import pytest
from commands import data_root, run_cli
from matching import canonical, card, problem, seeded, stored, template

from algo_coach.matches import MatchLog
from algo_coach.mint import generator_match


def run(monkeypatch, *argv: str) -> None:
    run_cli(monkeypatch, "gaps", *argv)


@pytest.fixture
def root(database, monkeypatch):
    """One card of two core forms, and a canonical displaying one of them."""
    data = data_root(database, monkeypatch)
    cards = seeded(data, card(templates=[template("fixed-window"), template("shrink-to-fit")]))
    stored(data, problem("p1", techniques=["sliding-window"]))
    # stored beside the problem, as its claim names it
    solution = canonical("p1")
    fixed = next(one.id for one in cards[0].templates if one.slug == "fixed-window")
    MatchLog(data).append(generator_match(fixed, solution.id))
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


def test_an_empty_store_reports_no_template(database, monkeypatch, capsys):
    data_root(database, monkeypatch)

    run(monkeypatch)

    assert "0 of 0 core template(s) carry no solution" in capsys.readouterr().out
