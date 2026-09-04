from importlib import import_module

import pytest
from generating import FakeWriter
from matching import card, seeded, template

from algo_coach import cli
from algo_coach.calls import CallLog
from algo_coach.generation import Corpus, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import ProblemStatus, RetirementReason

TRANSPORT = import_module("algo_coach.cli.transport")

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    return data


def landed(root, monkeypatch, **overrides):
    """One stored problem, written through the whole pipeline so every record a
    reader joins is there."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    (one,) = seeded(root, card(templates=[template("longest-valid-window", speedup=True)]))
    write_problems(
        FakeWriter(slow=SLOW, generator=BUILDS, **overrides),
        CallLog(root),
        one,
        one.templates[0],
        Corpus.at(root),
        outcomes=OutcomeLog(root),
    )
    (stored,) = ProblemStore(root).all()
    return stored


def reading(monkeypatch, *argv: str) -> None:
    monkeypatch.setattr("sys.argv", ["algo-coach", "problem", *argv])
    cli.main()


def test_the_corpus_is_listed_where_no_id_is_named(root, monkeypatch, capsys):
    """What a reader has to have before naming one."""
    stored = landed(root, monkeypatch)

    reading(monkeypatch)

    out = capsys.readouterr().out
    assert f"{stored.id}  longest-valid-window" in out
    assert "created" in out and "1 problem(s) stored" in out


def test_a_problem_is_read_whole_by_a_prefix_of_its_id(root, monkeypatch, capsys):
    """The statement, the cases that decide it, and every solution written for
    it."""
    stored = landed(root, monkeypatch)

    reading(monkeypatch, stored.id[:8])

    out = capsys.readouterr().out
    assert f"# {stored.title} ({stored.id})" in out
    assert stored.statement in out
    # the canonical, the reference and the clock, each headed by its role
    assert out.count("```python") == 3
    assert "### naive" in out


def test_the_page_names_what_the_run_left_and_what_it_matched(root, monkeypatch, capsys):
    """The site outcomes and the generator's own assertion are keyed to the
    problem, and are readable nowhere else."""
    stored = landed(root, monkeypatch)

    reading(monkeypatch, stored.id)

    out = capsys.readouterr().out
    assert "displays  generator" in out
    assert "separating at" in out
    # nothing has read a canonical, so the view is empty rather than absent
    assert "techniques: none read" in out


def test_a_retired_problem_names_the_reason(root, monkeypatch, capsys):
    """Readers treat the two retirements apart, so the status alone would not
    say whether its attempts count."""
    stored = landed(root, monkeypatch)
    ProblemStore(root).put(
        stored.model_copy(
            update={
                "status": ProblemStatus.RETIRED,
                "retired_reason": RetirementReason.TELEGRAPHED,
            }
        )
    )

    reading(monkeypatch)

    assert "retired: telegraphed" in capsys.readouterr().out


def test_a_problem_that_is_not_stored_says_so(root, monkeypatch, capsys):
    landed(root, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        reading(monkeypatch, "beef")

    assert exit_info.value.code == 1
    assert "no problem beef" in capsys.readouterr().err


def test_an_empty_corpus_says_so(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reading(monkeypatch)

    assert exit_info.value.code == 0
    assert "no problem is stored" in capsys.readouterr().err
