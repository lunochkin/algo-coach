from datetime import UTC, datetime, timedelta

import pytest

from algo_coach import cli
from algo_coach.cli.display import age
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    FailureMode,
    Problem,
    ProblemOwner,
)
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
            statement="Given an array, return ...",
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


def root_of(log: AttemptLog):
    return log.root


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


def push_when_asked(drill_root, monkeypatch, pushed: list, answers: list[str]) -> None:
    """Scripts a drill whose push lands while the loop is waiting."""
    scripted = iter(["1", *answers])

    def ask(prompt: str) -> str:
        if prompt.startswith("pushed?"):
            if not pushed:
                return "q"
            for record in pushed:
                drill_root.append_attempt(record)
            pushed.clear()
            return ""
        return next(scripted)

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    )
    cli.main()


def test_the_drill_reads_what_the_push_added(drill_root, monkeypatch, capsys):
    """The user pushes in another terminal; the loop re-reads its own log."""
    pushed = [attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))]
    push_when_asked(drill_root, monkeypatch, pushed, ["", ""])

    assert "1 attempt(s)" in capsys.readouterr().out


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
    assert "(0d)" in age(T0 + timedelta(hours=6), T0)


def test_the_drilled_technique_is_the_claims_default(drill_root, monkeypatch, capsys):
    """Enter accepts it: selection picked the problem by its tags, so what was
    practised is always a legal claim."""
    pushed = [attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))]
    push_when_asked(drill_root, monkeypatch, pushed, ["", ""])

    (claim,) = drill_root.claims()
    assert claim.techniques == ["greedy"]
    assert claim.source is ClaimSource.USER
    assert claim.attempt_id == "a3"


def test_a_label_is_recorded_as_its_own_record(drill_root, monkeypatch, capsys):
    pushed = [attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))]
    push_when_asked(drill_root, monkeypatch, pushed, ["", "3"])

    (label,) = drill_root.self_labels()
    assert (label.attempt_id, label.mode) == ("a3", FailureMode.GAP)


def test_skipping_records_neither(drill_root, monkeypatch, capsys):
    """Nothing invented: an unanswered question leaves no record."""
    pushed = [attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))]
    push_when_asked(drill_root, monkeypatch, pushed, ["s", "s"])

    assert drill_root.claims() == []
    assert drill_root.self_labels() == []


def test_each_attempt_of_a_sitting_is_asked_about(drill_root, monkeypatch, capsys):
    pushed = [
        attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200)),
        attempt("a4", "greedy-one", finished_at=T0 + timedelta(days=200, minutes=5)),
    ]
    push_when_asked(drill_root, monkeypatch, pushed, ["", "3", "", "5"])

    assert [label.mode for label in drill_root.self_labels()] == [
        FailureMode.GAP,
        FailureMode.NONE,
    ]
    assert len(drill_root.claims()) == 2


def test_the_previous_answer_becomes_the_next_default(drill_root, monkeypatch, capsys):
    pushed = [
        attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200)),
        attempt("a4", "greedy-one", finished_at=T0 + timedelta(days=200, minutes=5)),
    ]
    push_when_asked(drill_root, monkeypatch, pushed, ["", "2", "", ""])

    assert [label.mode for label in drill_root.self_labels()] == [
        FailureMode.RUST,
        FailureMode.RUST,
    ]


def test_a_takes_the_defaults_for_everything_remaining(drill_root, monkeypatch, capsys):
    """The long tail: one keystroke ends the questions without ending the drill."""
    pushed = [
        attempt(f"a{n}", "greedy-one", finished_at=T0 + timedelta(days=200, minutes=n))
        for n in range(3, 8)
    ]
    push_when_asked(drill_root, monkeypatch, pushed, ["", "2", "a"])

    assert len(drill_root.claims()) == 5
    assert {label.mode for label in drill_root.self_labels()} == {FailureMode.RUST}


def test_a_claim_can_name_several_techniques(drill_root, monkeypatch, capsys):
    """A solution can use more than one, so the answer takes a list."""
    seed_problem(root_of(drill_root), id="two-tags", tags=["Greedy", "Sorting"])
    pushed = [attempt("a3", "two-tags", finished_at=T0 + timedelta(days=200))]
    scripted = iter(["1", "1,2", "s"])

    def ask(prompt: str) -> str:
        if prompt.startswith("pushed?"):
            if not pushed:
                return "q"
            for record in pushed:
                drill_root.append_attempt(record)
            pushed.clear()
            return ""
        return next(scripted)

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    )
    cli.main()

    (claim,) = drill_root.claims()
    assert claim.techniques == ["greedy", "sorting"]


def test_a_bad_answer_is_asked_again(drill_root, monkeypatch, capsys):
    pushed = [attempt("a3", "greedy-one", finished_at=T0 + timedelta(days=200))]
    push_when_asked(drill_root, monkeypatch, pushed, ["nine", "", ""])

    assert "pick numbers between 1 and" in capsys.readouterr().out
    assert len(drill_root.claims()) == 1


def test_the_loop_records_a_decline_at_the_moment_of_solving(
    drill_root, monkeypatch, capsys
):
    """A claim is cheapest here, and so is a decline. Naming none of the tags
    is a verdict about the code, and the loop is where it is worth a keystroke
    rather than a re-read months later."""
    seed_problem(root_of(drill_root), id="two-tags", tags=["Greedy", "Sorting"])
    pushed = [attempt("a3", "two-tags", finished_at=T0 + timedelta(days=200))]
    scripted = iter(["1", "0", "s"])

    def ask(prompt: str) -> str:
        if prompt.startswith("pushed?"):
            if not pushed:
                return "q"
            for record in pushed:
                drill_root.append_attempt(record)
            pushed.clear()
            return ""
        return next(scripted)

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    )
    cli.main()

    (claim,) = drill_root.claims()
    assert (claim.techniques, claim.declined) == ([], True)


def test_a_skipped_claim_is_still_no_claim(drill_root, monkeypatch, capsys):
    """The trap the flag exists to avoid. `if claimed:` reads a stated empty
    list as nothing answered, so the two need telling apart on the write path
    and not only in the schema."""
    seed_problem(root_of(drill_root), id="two-tags", tags=["Greedy", "Sorting"])
    pushed = [attempt("a3", "two-tags", finished_at=T0 + timedelta(days=200))]
    scripted = iter(["1", "s", "s"])

    def ask(prompt: str) -> str:
        if prompt.startswith("pushed?"):
            if not pushed:
                return "q"
            for record in pushed:
                drill_root.append_attempt(record)
            pushed.clear()
            return ""
        return next(scripted)

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    )
    cli.main()

    assert drill_root.claims() == []


def test_the_none_key_is_shown_beside_the_candidates(drill_root, monkeypatch, capsys):
    """Only the techniques question takes it. A legend over both would offer
    the labels a key their prompt rejects."""
    seed_problem(root_of(drill_root), id="two-tags", tags=["Greedy", "Sorting"])
    pushed = [attempt("a3", "two-tags", finished_at=T0 + timedelta(days=200))]
    # `choose` re-asks until a number lands, so the problem pick comes first.
    scripted = iter(["1", "s", "s"])

    def ask(prompt: str) -> str:
        if prompt.startswith("pushed?"):
            if not pushed:
                return "q"
            for record in pushed:
                drill_root.append_attempt(record)
            pushed.clear()
            return ""
        return next(scripted)

    monkeypatch.setattr("builtins.input", ask)
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "drill", "--user", "u1", "--technique", "greedy"]
    )
    cli.main()

    lines = capsys.readouterr().out.splitlines()
    (techniques,) = [line for line in lines if line.strip().startswith("techniques")]
    (labels,) = [line for line in lines if line.strip().startswith("labels")]
    assert "0 for none of these" in techniques
    assert "0 for" not in labels
