from datetime import UTC, datetime, timedelta

import pytest

from algo_coach import cli
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, AttemptOrigin, Problem, ProblemOwner
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def seed_problem(root, *, id: str, tags: list[str], title: str | None = None) -> None:
    ProblemStore(root).put(
        Problem(
            id=id,
            external_id=f"ext-{id}",
            user_id="u1",
            owner=ProblemOwner.USER,
            title=title or id,
            title_slug=id,
            url=f"https://example.invalid/{id}",
            source_tags=tags,
            techniques=map_tags(tags),
        )
    )


def attempt(
    id: str, problem_id: str, *, finished_at: datetime = T0, solved: bool = True
) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=solved,
        origin=AttemptOrigin.PUSH,
    )


@pytest.fixture
def drill_root(tmp_path, monkeypatch) -> AttemptLog:
    """One greedy problem attempted long ago, one trie problem attempted since,
    so the stale ordering has something to say."""
    root = tmp_path / "data"
    seed_problem(root, id="greedy-one", tags=["Greedy"], title="Can Place Flowers")
    seed_problem(root, id="trie-one", tags=["Trie"], title="Implement Trie")
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "greedy-one", finished_at=T0))
    log.append_attempt(attempt("a2", "trie-one", finished_at=T0 + timedelta(days=30)))
    return log


def run(monkeypatch, answers: list[str], *argv: str) -> None:
    scripted = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(scripted))
    monkeypatch.setattr("sys.argv", ["algo-coach", "drill", "--user", "u1", *argv])
    cli.main()


def test_drill_offers_the_stalest_technique_first(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["1", "1", "q"])

    out = capsys.readouterr().out
    first, second = out.splitlines()[0], out.splitlines()[1]
    assert "greedy" in first
    assert "trie" in second


def test_drill_hands_over_the_problem_and_its_history(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["1", "1", "q"])

    out = capsys.readouterr().out
    assert "Can Place Flowers — greedy" in out
    assert "https://example.invalid/greedy-one" in out
    assert "solved 1/1" in out


def test_ending_before_a_push_records_nothing(drill_root, monkeypatch, capsys):
    """Quitting is not a failure — there is simply nothing to key a claim to."""
    run(monkeypatch, ["1", "1", "q"])

    assert "nothing recorded" in capsys.readouterr().out


def test_the_drill_reads_what_the_push_added(drill_root, monkeypatch, capsys):
    """The user pushes in another terminal; the loop re-reads its own log."""
    pushed = attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))

    def answer(_):
        drill_root.append_attempt(pushed)
        return ""

    argv = ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    monkeypatch.setattr("sys.argv", argv)
    choices = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(choices, None) or answer(prompt))
    cli.main()

    assert "1 attempt appeared" in capsys.readouterr().out


def test_a_push_that_added_nothing_asks_again(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["1", "1", "", "q"])

    assert "nothing new in the log for this problem" in capsys.readouterr().out


def test_end_of_input_while_waiting_ends_the_drill(drill_root, monkeypatch, capsys):
    answers = iter(["1", "1"])

    def ask(_):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr("sys.argv", ["algo-coach", "drill", "--user", "u1"])
    cli.main()

    assert "nothing recorded" in capsys.readouterr().out


def test_technique_flag_skips_the_first_prompt(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["1", "q"], "--technique", "trie")

    assert "Implement Trie — trie" in capsys.readouterr().out


def test_a_bad_choice_is_asked_again(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["nine", "0", "2", "1", "q"])

    out = capsys.readouterr().out
    assert out.count("pick a number between 1 and 2") == 2
    assert "Implement Trie — trie" in out


def test_end_of_input_ends_the_drill(drill_root, monkeypatch, capsys):
    """Piped or interrupted: choosing for the user would start a drill nobody
    asked for."""

    def eof(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    monkeypatch.setattr("sys.argv", ["algo-coach", "drill", "--user", "u1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "no technique chosen" in capsys.readouterr().err


def test_a_technique_no_problem_carries(drill_root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [], "--technique", "binary-search")

    assert exit_info.value.code == 1
    assert "no problem carries binary-search" in capsys.readouterr().err


def test_an_empty_log_has_nothing_to_drill(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 1
    assert "no attempts for u1" in capsys.readouterr().err


def test_limit_caps_the_choices(drill_root, monkeypatch, capsys):
    run(monkeypatch, ["1", "1", "q"], "--limit", "1")

    out = capsys.readouterr().out
    assert "trie" not in out.splitlines()[0]
    assert "technique [1-1]" not in out  # the prompt goes to stdin's echo, not stdout


def test_a_named_technique_drills_a_store_with_no_attempts(tmp_path, monkeypatch, capsys):
    """A fresh store has no board to choose from, but a problem is still
    drillable when the technique is named outright."""
    root = tmp_path / "data"
    seed_problem(root, id="fresh-one", tags=["Greedy"], title="Can Place Flowers")
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    run(monkeypatch, ["1", "q"], "--technique", "greedy")

    out = capsys.readouterr().out
    assert "Can Place Flowers — greedy" in out
    assert "never attempted" in out


def test_an_empty_board_says_what_to_do_instead(drill_root, monkeypatch, capsys):
    monkeypatch.setattr(cli, "DATA_ROOT", drill_root.root.parent / "empty")

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 1
    assert "name a technique to drill" in capsys.readouterr().err


def test_an_attempt_stamped_later_today_is_not_negatively_old():
    """The platform's clock can be ahead of the reader's within a day."""
    assert "(0d)" in cli._age(T0 + timedelta(hours=6), T0)
