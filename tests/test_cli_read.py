import pytest
from commands import data_root, run_cli
from helpers import FakeTransport, Verdict
from matching import canonicals, problem, stored

from algo_coach.classifier import EFFORT, MODEL
from algo_coach.readings import ReadingLog
from algo_coach.solutions import SolutionLog


def run(monkeypatch, client: FakeTransport, *argv: str) -> None:
    run_cli(monkeypatch, "read", *argv, client=client)


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = data_root(tmp_path, monkeypatch)
    corpus = stored(data, problem("p1", techniques=[]))
    for one in canonicals(*corpus):
        SolutionLog(data).append(one)
    return data


def test_the_command_reads_the_corpus(root, monkeypatch, capsys):
    run(monkeypatch, FakeTransport.answering(Verdict(["sorting"])))

    assert [one.techniques for one in ReadingLog(root).readings()] == [["sorting"]]
    assert f"1 canonical(s) read by {MODEL}, effort {EFFORT}" in capsys.readouterr().out


def test_a_second_run_reads_nothing(root, monkeypatch, capsys):
    """The digest is what a skip keys on, so a corpus that has not moved costs
    no call the second time."""
    run(monkeypatch, FakeTransport.answering(Verdict(["sorting"])))
    capsys.readouterr()

    run(monkeypatch, FakeTransport.answering())

    assert len(ReadingLog(root).readings()) == 1
    assert "0 canonical(s) read" in capsys.readouterr().out


def test_a_run_that_landed_nothing_exits_nonzero(root, monkeypatch, capsys):
    client = FakeTransport.answering(Verdict(error=RuntimeError("bad key")))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "bad key" in capsys.readouterr().err


def test_the_progress_line_names_the_problem(root, monkeypatch, capsys):
    """A minted solution id names nothing a reader recognises."""
    run(monkeypatch, FakeTransport.answering(Verdict(["sorting"])))

    assert "p1" in capsys.readouterr().err
