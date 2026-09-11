import pytest
from commands import connected, run_cli

from algo_coach.log import invitations_held, invite, invited, withdraw


def test_an_invited_email_is_matched_whatever_its_case(database):
    """A provider hands back an email in whatever case its account holds."""
    invite(database, "Solver@Example.com")

    assert invited(database, "solver@EXAMPLE.com")
    assert not invited(database, "other@example.com")


def test_inviting_an_email_twice_holds_one_invitation(database):
    invite(database, "solver@example.com")
    invite(database, "SOLVER@example.com")

    assert invitations_held(database) == ["solver@example.com"]


def test_a_withdrawn_invitation_lets_nobody_in(database):
    invite(database, "solver@example.com")

    assert withdraw(database, "Solver@example.com")
    assert not invited(database, "solver@example.com")
    assert not withdraw(database, "solver@example.com")


def test_the_terminal_invites_lists_and_withdraws(database, monkeypatch, capsys):
    connected(database, monkeypatch)

    run_cli(monkeypatch, "invite", "add", "Solver@Example.com")
    run_cli(monkeypatch, "invite", "list")
    run_cli(monkeypatch, "invite", "remove", "solver@example.com")
    run_cli(monkeypatch, "invite", "list")

    assert capsys.readouterr().out.splitlines() == [
        "invited solver@example.com",
        "solver@example.com",
        "withdrew solver@example.com",
        "no email is invited",
    ]


def test_withdrawing_an_email_never_invited_says_so(database, monkeypatch, capsys):
    connected(database, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "invite", "remove", "nobody@example.com")

    assert exit_info.value.code == 1
    assert "never invited" in capsys.readouterr().err
