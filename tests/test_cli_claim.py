from datetime import UTC, datetime, timedelta

import pytest

from algo_coach import cli
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    Problem,
    ProblemOwner,
    TechniqueClaim,
)
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def seed_problem(root, *, id: str, tags: list[str]) -> None:
    ProblemStore(root).put(
        Problem(
            id=id,
            external_id=f"ext-{id}",
            user_id="u1",
            owner=ProblemOwner.USER,
            title=id,
            title_slug=id,
            source_tags=tags,
            techniques=map_tags(tags),
        )
    )


def attempt(
    id: str,
    problem_id: str,
    *,
    code: str | None = "def f(): pass",
    finished_at: datetime = T0,
) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=True,
        origin=AttemptOrigin.PUSH,
        code=code,
    )


@pytest.fixture
def claim_root(tmp_path, monkeypatch) -> AttemptLog:
    """One two-tag problem and one single-tag problem, an attempt on each."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    seed_problem(root, id="one-tag", tags=["Trie"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-tags"))
    log.append_attempt(attempt("a2", "one-tag"))
    return log


def run(monkeypatch, answers: list[str], *argv: str) -> None:
    scripted = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(scripted))
    monkeypatch.setattr("sys.argv", ["algo-coach", "claim", "--user", "u1", *argv])
    cli.main()


def test_a_claim_records_what_was_chosen(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1"])

    (claim,) = claim_root.claims()
    assert claim.attempt_id == "a1"
    assert claim.techniques == ["greedy"]
    assert claim.source is ClaimSource.USER
    assert claim.model is None


def test_several_techniques_can_be_named(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1,2"])

    (claim,) = claim_root.claims()
    assert claim.techniques == ["greedy", "sorting"]


def test_a_single_tag_problem_is_never_offered(claim_root, monkeypatch, capsys):
    """Its fallback already answers; a claim there disputes nothing."""
    run(monkeypatch, ["1"])

    out = capsys.readouterr().out
    assert "two-tags" in out
    assert "one-tag" not in out


def test_skipping_writes_nothing(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["s"])

    assert claim_root.claims() == []
    assert "0 claim(s) written" in capsys.readouterr().out


def test_an_already_claimed_attempt_is_not_asked_again(claim_root, monkeypatch, capsys):
    claim_root.append_claim(
        TechniqueClaim(
            id="c1",
            created_at=T0,
            attempt_id="a1",
            techniques=["greedy"],
            source=ClaimSource.USER,
        )
    )

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 1
    assert "nothing left to claim" in capsys.readouterr().err


def test_an_attempt_without_code_is_not_offered(tmp_path, monkeypatch, capsys):
    """The evidence is the code; without it there is nothing to read."""
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    AttemptLog(root).append_attempt(attempt("a1", "two-tags", code=None))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 1


def test_the_code_is_shown(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1"])

    assert "def f(): pass" in capsys.readouterr().out


def test_a_long_solution_is_cut_and_says_so(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    AttemptLog(root).append_attempt(attempt("a1", "two-tags", code="\n".join("x" * 50)))

    run(monkeypatch, ["1"], "--lines", "10")

    assert "... 40 more lines" in capsys.readouterr().out


def retried(root, monkeypatch, *attempts: Attempt) -> AttemptLog:
    """Several attempts on one two-tag problem — a problem that took retries."""
    seed_problem(root, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    log = AttemptLog(root)
    for one in attempts:
        log.append_attempt(one)
    return log


def test_a_problem_contributes_one_attempt(tmp_path, monkeypatch, capsys):
    """A retry asks the identical question — same solution, same candidate
    tags — so counting both would weight that problem twice."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-tags"),
        attempt("a2", "two-tags"),
        attempt("a3", "two-tags"),
    )

    run(monkeypatch, ["1"], "--count", "3")

    assert len(log.claims()) == 1
    assert "1 claim(s) written" in capsys.readouterr().out


def test_the_latest_attempt_is_the_one_offered(tmp_path, monkeypatch, capsys):
    """The solution that stands. An earlier one may show an approach that was
    abandoned, and the claim worth scoring is the one the board credits."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-tags", finished_at=T0),
        attempt("a2", "two-tags", finished_at=T0 + timedelta(days=2)),
        attempt("a3", "two-tags", finished_at=T0 + timedelta(days=1)),
    )

    run(monkeypatch, ["1"])

    (claim,) = log.claims()
    assert claim.attempt_id == "a2"


def test_the_id_breaks_a_tie_on_the_same_timestamp(tmp_path, monkeypatch, capsys):
    """Same order the drill loop reads a sitting in, so one rule decides
    'latest' wherever the log is grouped."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a3", "two-tags"),
        attempt("a1", "two-tags"),
        attempt("a2", "two-tags"),
    )

    run(monkeypatch, ["1"])

    (claim,) = log.claims()
    assert claim.attempt_id == "a3"


def test_an_earlier_attempt_stands_in_when_the_latest_has_no_code(tmp_path, monkeypatch, capsys):
    """The latest *carrying code*: a push without code is no evidence, and
    dropping the problem over it would lose a solution that is still readable."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-tags", finished_at=T0),
        attempt("a2", "two-tags", finished_at=T0 + timedelta(days=1), code=None),
    )

    run(monkeypatch, ["1"])

    (claim,) = log.claims()
    assert claim.attempt_id == "a1"


def test_a_problem_leaves_the_pool_once_its_attempt_is_claimed(tmp_path, monkeypatch, capsys):
    """Its older attempts are not a second question — offering one would ask
    what a claim already answered."""
    retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-tags", finished_at=T0),
        attempt("a2", "two-tags", finished_at=T0 + timedelta(days=1)),
    )

    run(monkeypatch, ["1"])
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 1


def seed_many(root, count: int) -> AttemptLog:
    """`count` two-tag problems, an attempt on each — a pool the sample draws
    from, since a problem contributes one attempt however many it holds."""
    log = AttemptLog(root)
    for n in range(count):
        seed_problem(root, id=f"p{n}", tags=["Greedy", "Sorting"])
        log.append_attempt(attempt(f"a{n}", f"p{n}"))
    return log


def test_count_caps_how_many_are_asked_about(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    log = seed_many(root, 5)

    run(monkeypatch, ["1", "1"], "--count", "2")

    assert len(log.claims()) == 2


def test_the_technique_flag_narrows_the_pool(claim_root, monkeypatch, capsys):
    seed_problem(claim_root.root, id="tries", tags=["Trie", "Sorting"])
    claim_root.append_attempt(attempt("a3", "tries"))

    run(monkeypatch, ["1"], "--technique", "trie", "--count", "1")

    (claim,) = claim_root.claims()
    assert claim.attempt_id == "a3"


def seeded_store(root, monkeypatch) -> AttemptLog:
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    return seed_many(root, 6)


def test_the_same_seed_asks_in_the_same_order(tmp_path, monkeypatch, capsys):
    """Two identical logs, same seed, same sequence — so a sample can be
    described by its seed rather than by listing what it held."""
    first = seeded_store(tmp_path / "one", monkeypatch)
    run(monkeypatch, ["1", "1", "1"], "--count", "3")
    second = seeded_store(tmp_path / "two", monkeypatch)
    run(monkeypatch, ["1", "1", "1"], "--count", "3")

    assert [claim.attempt_id for claim in first.claims()] == [
        claim.attempt_id for claim in second.claims()
    ]


def test_a_claimed_attempt_drops_out_of_the_pool(tmp_path, monkeypatch, capsys):
    """Successive runs make progress rather than re-asking."""
    log = seeded_store(tmp_path / "one", monkeypatch)
    run(monkeypatch, ["1"], "--count", "1")
    run(monkeypatch, ["1"], "--count", "1")

    claimed = [claim.attempt_id for claim in log.claims()]
    assert len(set(claimed)) == 2


def test_ending_early_keeps_what_landed(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    log = seed_many(root, 4)

    run(monkeypatch, ["1", "a"])

    assert len(log.claims()) == 1
    assert "1 claim(s) written" in capsys.readouterr().out


def test_the_candidates_are_shown(claim_root, monkeypatch, capsys):
    """They differ per problem, so they cannot be printed once up front."""
    run(monkeypatch, ["1"])

    out = capsys.readouterr().out
    assert "1 greedy" in out
    assert "2 sorting" in out
