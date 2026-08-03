import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import import_module

import pytest

from algo_coach import cli
from algo_coach.claims import MODEL
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, AttemptOrigin, Problem, ProblemOwner
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class FakeMessages:
    techniques: list[str] | None
    error: Exception | None = None
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        text = json.dumps({"techniques": self.techniques})
        return type(
            "Response",
            (),
            {"content": [type("Block", (), {"type": "text", "text": text})()]},
        )()


@dataclass
class FakeClient:
    messages: FakeMessages


# By module, not by dotted string: `algo_coach.cli.classify` resolves to the
# command the package re-exports, which shadows the module of the same name.
COMMAND = import_module("algo_coach.cli.classify")


def run(monkeypatch, client: FakeClient, *argv: str) -> None:
    monkeypatch.setattr(COMMAND, "Anthropic", lambda: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1", *argv])
    cli.main()


def attempt(id: str, problem_id: str) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id="u1",
        problem_id=problem_id,
        finished_at=T0,
        solved=True,
        origin=AttemptOrigin.PUSH,
        code="def f(): pass",
    )


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    tags = ["Greedy", "Sorting"]
    ProblemStore(data).put(
        Problem(
            id="two-tags",
            external_id="ext-two-tags",
            user_id="u1",
            owner=ProblemOwner.USER,
            title="two-tags",
            title_slug="two-tags",
            source_tags=tags,
            techniques=map_tags(tags),
        )
    )
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-tags"))
    return data


def test_the_command_claims_the_backlog(root, monkeypatch, capsys):
    run(monkeypatch, FakeClient(FakeMessages(["greedy"])))

    (claim,) = AttemptLog(root).claims()
    assert claim.techniques == ["greedy"]
    assert f"1 claim(s) written by {MODEL}" in capsys.readouterr().out


def test_a_run_that_landed_nothing_exits_nonzero(root, monkeypatch, capsys):
    """A key that does not work fails every attempt in turn — silence and a
    zero exit would read as a backlog with nothing left to claim."""
    client = FakeClient(FakeMessages(None, error=RuntimeError("bad key")))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "bad key" in capsys.readouterr().out


def test_the_limit_caps_the_run(root, monkeypatch, capsys):
    AttemptLog(root).append_attempt(attempt("a2", "two-tags"))
    client = FakeClient(FakeMessages(["greedy"]))

    run(monkeypatch, client, "--limit", "1")

    assert len(client.messages.calls) == 1
    assert len(AttemptLog(root).claims()) == 1
