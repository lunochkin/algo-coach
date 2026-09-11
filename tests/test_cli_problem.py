import pytest
from commands import data_root, run_cli
from generating import FakeWriter
from matching import card, seeded, template

from algo_coach.calls import CallLog
from algo_coach.generation import Corpus, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import ProblemStatus, RetirementReason

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"


@pytest.fixture
def root(database, monkeypatch):
    data = data_root(database, monkeypatch)
    return data


def landed(root, monkeypatch, **overrides):
    """One stored problem, written through the whole pipeline so every record a
    reader joins is there."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
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


def shown(monkeypatch, *argv: str) -> None:
    run_cli(monkeypatch, "problem", *argv)


def test_the_corpus_is_listed_where_no_id_is_named(root, monkeypatch, capsys):
    """What a reader has to have before naming one."""
    stored = landed(root, monkeypatch)

    shown(monkeypatch)

    out = capsys.readouterr().out
    assert f"{stored.id}  longest-valid-window" in out
    assert "created" in out and "1 problem(s) stored" in out


def test_a_problem_is_read_whole_by_a_prefix_of_its_id(root, monkeypatch, capsys):
    """The statement, the cases that decide it, and every solution written for
    it."""
    stored = landed(root, monkeypatch)

    shown(monkeypatch, stored.id[:8])

    out = capsys.readouterr().out
    assert f"# {stored.title} ({stored.id})" in out
    assert stored.statement in out
    # the canonical, the reference and the naive solution, each headed by its
    # role
    assert out.count("```python") == 3
    assert "### naive" in out


def test_the_page_names_what_the_run_left_and_what_it_matched(root, monkeypatch, capsys):
    """The site outcomes and the generator's own assertion are keyed to the
    problem, and are readable nowhere else."""
    stored = landed(root, monkeypatch)

    shown(monkeypatch, stored.id)

    out = capsys.readouterr().out
    assert "displays  generator" in out
    assert "separating at" in out
    # the bound the size was searched under, which the cleared draft no longer
    # carries
    assert "up to" in out
    # nothing has read a canonical, so the view is empty rather than absent
    assert "techniques: none read" in out


def test_a_retired_problem_names_the_reason(root, monkeypatch, capsys):
    """The reason decides whether its attempts count, so the status alone would
    not do."""
    stored = landed(root, monkeypatch)
    ProblemStore(root).put(
        stored.model_copy(
            update={
                "status": ProblemStatus.RETIRED,
                "retired_reason": RetirementReason.DEFECTIVE,
            }
        )
    )

    shown(monkeypatch)

    assert "retired: defective" in capsys.readouterr().out


def test_a_problem_that_is_not_stored_says_so(root, monkeypatch, capsys):
    landed(root, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch, "beef")

    assert exit_info.value.code == 1
    assert "no problem beef" in capsys.readouterr().err


def test_an_empty_corpus_says_so(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch)

    assert exit_info.value.code == 0
    assert "no problem is stored" in capsys.readouterr().err


def answering(monkeypatch, reply: str | None) -> None:
    """The confirmation prompt, answered. `None` is the input closing."""

    def given(_prompt: str) -> str:
        if reply is None:
            raise EOFError
        return reply

    monkeypatch.setattr("builtins.input", given)


def test_a_confirmed_retirement_moves_the_status(root, monkeypatch, capsys):
    """The problem is read whole before the question, since the verdict is that
    this statement asks for something its cases do not decide."""
    stored = landed(root, monkeypatch)
    answering(monkeypatch, "y")

    shown(monkeypatch, "--retire", stored.id[:8])

    out = capsys.readouterr().out
    assert out.index(stored.statement) < out.index("retired: defective")
    retired = ProblemStore(root).get(stored.id)
    assert (retired.status, retired.retired_reason) == (
        ProblemStatus.RETIRED,
        RetirementReason.DEFECTIVE,
    )


@pytest.mark.parametrize("reply", ["n", "", "yes please", None])
def test_anything_but_yes_retires_nothing(root, monkeypatch, capsys, reply):
    """Every user is served the problem, so a stray key or a closed input may
    not take it away from them."""
    stored = landed(root, monkeypatch)
    answering(monkeypatch, reply)

    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch, "--retire", stored.id)

    assert exit_info.value.code == 0
    assert "nothing retired" in capsys.readouterr().err
    assert ProblemStore(root).get(stored.id).status is ProblemStatus.CREATED


def test_a_retired_problem_is_not_asked_about_again(root, monkeypatch, capsys):
    stored = landed(root, monkeypatch)
    ProblemStore(root).retire(stored.id, RetirementReason.DEFECTIVE)
    monkeypatch.setattr("builtins.input", lambda _prompt: pytest.fail("asked again"))

    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch, "--retire", stored.id)

    assert exit_info.value.code == 0
    assert "already retired: defective" in capsys.readouterr().err


def test_retiring_an_unknown_problem_says_so(root, monkeypatch, capsys):
    landed(root, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch, "--retire", "beef")

    assert exit_info.value.code == 1
    assert "no problem beef" in capsys.readouterr().err


def test_retire_takes_no_second_id(root, monkeypatch, capsys):
    """`--retire` names the problem, so a positional id beside it is two answers
    to one question."""
    stored = landed(root, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        shown(monkeypatch, stored.id, "--retire", stored.id)

    assert exit_info.value.code == 2
    assert ProblemStore(root).get(stored.id).status is ProblemStatus.CREATED
