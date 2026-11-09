import importlib

import pytest
from commands import connected, run_cli
from generating import SLOW, FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog
from algo_coach.generation import Corpus, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.runner import runner

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"


@pytest.fixture
def root(database, monkeypatch):
    return connected(database, monkeypatch)


def landed(root, monkeypatch):
    """One stored problem, written through the whole pipeline, so its canonical
    and the cases that decide it are both there."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    (one,) = seeded(root, card(templates=[template("longest-valid-window", speedup=True)]))
    write_problems(
        FakeWriter(slow=SLOW, generator=BUILDS),
        CallLog(root),
        one,
        one.templates[0],
        Corpus.at(root),
        outcomes=OutcomeLog(root),
    )
    (stored,) = ProblemStore(root).all()
    return stored


def test_a_canonical_passing_every_case_within_the_bar_lists_no_case(root, monkeypatch, capsys):
    """The run names its runner and cap, since a timing is comparable only
    within one runner."""
    landed(root, monkeypatch)

    run_cli(monkeypatch, "retime")

    first, *listed, last = capsys.readouterr().out.splitlines()
    assert first == f"runner {runner()}, cap 2000 ms, bar 200 ms"
    assert listed == []
    assert last.startswith("0 of ")


def test_a_case_past_the_bar_is_listed_by_problem_canonical_and_case(root, monkeypatch, capsys):
    """Each listed case is one a correct submission a few percent slower would
    fail, so the listing names exactly where to look."""
    stored = landed(root, monkeypatch)
    # the module itself: the package's own `retime` names the command's function
    monkeypatch.setattr(importlib.import_module("algo_coach.cli.retime"), "BAR_MS", -1)

    run_cli(monkeypatch, "retime")

    _, *listed, _ = capsys.readouterr().out.splitlines()
    cases = Corpus.at(root).cases.for_problem(stored.id)
    assert len(listed) == len(cases)
    assert all(line.startswith(f"{stored.id}  ") for line in listed)
