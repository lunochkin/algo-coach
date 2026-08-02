import json
from datetime import UTC, datetime, timedelta

import pytest

from algo_coach import cli
from algo_coach.board import TechniqueRow
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    FailureMode,
    Problem,
    ProblemOwner,
    TechniqueClaim,
)
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def board_root(tmp_path, monkeypatch) -> AttemptLog:
    """A store holding one greedy problem, and a log of attempts on it."""
    root = tmp_path / "data"
    tags = ["Greedy", "Sorting"]
    ProblemStore(root).put(
        Problem(
            id="minted-u1",
            external_id="p1",
            user_id="u1",
            owner=ProblemOwner.USER,
            title="Two Sum",
            title_slug="two-sum",
            source_tags=tags,
            techniques=map_tags(tags),
        )
    )
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    return AttemptLog(root)


def attempt(id: str, *, user_id: str = "u1", solved: bool = True, self_label=None) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id=user_id,
        problem_id="minted-u1",
        finished_at=T0,
        solved=solved,
        origin=AttemptOrigin.PUSH,
        self_label=self_label,
    )


def run(monkeypatch, *argv: str) -> None:
    monkeypatch.setattr("sys.argv", ["algo-coach", "board", *argv])
    cli.main()


def test_board_renders_a_row_per_technique(board_root, monkeypatch, capsys):
    board_root.append_attempt(attempt("a1", solved=False, self_label=FailureMode.RUST))
    board_root.append_attempt(attempt("a2"))

    run(monkeypatch, "--user", "u1")

    header, greedy, sorting = capsys.readouterr().out.splitlines()
    assert header.split() == ["technique", "attempts", "solved", "last", "labels"]
    assert greedy.split()[:4] == ["greedy", "2", "1/2", "2026-01-01"]
    assert greedy.endswith("rust:1")
    assert sorting.startswith("sorting")


def test_the_last_column_dates_an_attempt_and_ages_it():
    """Recency is what the board is read for; a date alone needs arithmetic."""
    row = TechniqueRow(
        technique="greedy",
        attempt_count=1,
        solved_count=1,
        last_attempt_at=T0,
    )

    (_, line) = cli._render([row], now=T0 + timedelta(days=9)).splitlines()

    assert "2026-01-01 (9d)" in line


def test_board_json_carries_the_rows(board_root, monkeypatch, capsys):
    board_root.append_attempt(attempt("a1"))

    run(monkeypatch, "--user", "u1", "--json")

    rows = json.loads(capsys.readouterr().out)
    assert [(row["technique"], row["attempt_count"]) for row in rows] == [
        ("greedy", 1),
        ("sorting", 1),
    ]


def test_board_counts_only_the_users_own_attempts(board_root, monkeypatch, capsys):
    board_root.append_attempt(attempt("a1", user_id="u1"))
    board_root.append_attempt(attempt("a2", user_id="u2"))

    run(monkeypatch, "--user", "u1", "--json")

    assert {row["attempt_count"] for row in json.loads(capsys.readouterr().out)} == {1}


def test_board_follows_a_claim_over_the_problems_tags(board_root, monkeypatch, capsys):
    board_root.append_attempt(attempt("a1"))
    board_root.append_claim(
        TechniqueClaim(
            id="c1",
            created_at=T0,
            attempt_id="a1",
            techniques=["two-pointers"],
            source=ClaimSource.USER,
        )
    )

    run(monkeypatch, "--user", "u1", "--json")

    assert [row["technique"] for row in json.loads(capsys.readouterr().out)] == ["two-pointers"]


def test_board_on_an_empty_log_says_so(board_root, monkeypatch, capsys):
    run(monkeypatch, "--user", "u1")

    assert "no attempts" in capsys.readouterr().out


def test_render_pads_every_column(board_root, monkeypatch, capsys):
    """A technique shorter than the header still lines up under it."""
    board_root.append_attempt(attempt("a1"))

    run(monkeypatch, "--user", "u1")

    header, *rows = capsys.readouterr().out.splitlines()
    assert all(line.index("2026-01-01") == header.index("last") for line in rows)
