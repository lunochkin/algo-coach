from datetime import UTC, datetime, timedelta

import pytest
from helpers import GENERATED

from algo_coach import cli
from algo_coach.classifier import PIN, TEMPERATURE, request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim, user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    ClaimSource,
    Kind,
    Problem,
    TechniqueClaim,
)
from algo_coach.techniques import criteria, criterion, standing_claims

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def seed_problem(root, *, id: str, techniques: list[str]) -> None:
    """Codes in the order given: a problem's own order is what the candidates
    are offered in."""
    ProblemStore(root).put(
        Problem(
            id=id,
            title=id,
            statement="Given an array, return ...",
            techniques=techniques,
            **GENERATED,
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
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=True,
        code=code,
    )


@pytest.fixture
def claim_root(tmp_path, monkeypatch) -> AttemptLog:
    """One two-tag problem and one single-tag problem, an attempt on each."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    seed_problem(root, id="one-tag", techniques=["trie"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)

    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "two-codes"))
    log.append_attempt(attempt("a2", "one-tag"))
    return log


def run(monkeypatch, answers: list[str], *argv: str) -> None:
    scripted = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(scripted))
    monkeypatch.setattr("sys.argv", ["algo-coach", "claim", "--user", "u1", *argv])
    cli.main()


def test_a_claim_records_what_was_chosen(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1", ""])

    (claim,) = claim_root.claims()
    assert claim.attempt_id == "a1"
    assert claim.techniques == ["greedy"]
    assert claim.source is ClaimSource.USER
    assert claim.model is None


def test_several_techniques_can_be_named(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1,2", ""])

    (claim,) = claim_root.claims()
    assert claim.techniques == ["greedy", "sorting"]


def test_a_single_tag_problem_is_never_offered(claim_root, monkeypatch, capsys):
    """Its fallback already answers; a claim there disputes nothing."""
    run(monkeypatch, ["1", ""])

    out = capsys.readouterr().out
    assert "two-codes" in out
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

    assert exit_info.value.code == 0
    assert "nothing left to claim" in capsys.readouterr().err


def test_a_machine_claimed_attempt_is_still_offered(claim_root, monkeypatch, capsys):
    """The classifier fills what no hand reached, and a user claim is what
    corrects it — so a machine claim leaves the attempt in the pool. A pool
    that emptied as the classifier ran would freeze the eval set at whatever
    was labelled before the first run."""
    claim_root.append_claim(
        classifier_claim(
            "a1",
            ["sorting"],
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )

    run(monkeypatch, ["1", ""])

    standing = standing_claims(claim_root.claims())["a1"]
    assert (standing.techniques, standing.source) == (["greedy"], ClaimSource.USER)


def test_the_machine_verdict_is_never_shown(claim_root, monkeypatch, capsys):
    """Reviewing an answer is the same labour as making one, but anchors on
    it: a plausible wrong call gets waved through. The question is asked from
    the code and the tags, as it would be with nothing claimed."""
    claim_root.append_claim(
        classifier_claim(
            "a1",
            ["sorting"],
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )

    run(monkeypatch, ["1", ""])

    shown = capsys.readouterr().out
    assert "a-model" not in shown
    assert "classifier" not in shown
    # The candidates are the problem's tags, in the problem's order — not the
    # claim's set, which would put what the machine chose first.
    assert "1 greedy   2 sorting" in shown


def test_an_attempt_without_code_is_not_offered(tmp_path, monkeypatch, capsys):
    """The evidence is the code; without it there is nothing to read."""
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    AttemptLog(root).append_attempt(attempt("a1", "two-codes", code=None))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 0


def test_the_code_is_shown(claim_root, monkeypatch, capsys):
    run(monkeypatch, ["1", ""])

    assert "def f(): pass" in capsys.readouterr().out


def test_a_long_solution_is_cut_and_says_so(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    AttemptLog(root).append_attempt(attempt("a1", "two-codes", code="\n".join("x" * 50)))

    run(monkeypatch, ["1", ""], "--lines", "10")

    assert "... 40 more lines" in capsys.readouterr().out


def retried(root, monkeypatch, *attempts: Attempt) -> AttemptLog:
    """Several attempts on one two-tag problem — a problem that took retries."""
    seed_problem(root, id="two-codes", techniques=["greedy", "sorting"])
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
        attempt("a1", "two-codes"),
        attempt("a2", "two-codes"),
        attempt("a3", "two-codes"),
    )

    run(monkeypatch, ["1", ""], "--count", "3")

    assert len(log.claims()) == 1
    assert "1 claim(s) written" in capsys.readouterr().out


def test_the_latest_attempt_is_the_one_offered(tmp_path, monkeypatch, capsys):
    """The solution that stands. An earlier one may show an approach that was
    abandoned, and the claim worth scoring is the one the board credits."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-codes", finished_at=T0),
        attempt("a2", "two-codes", finished_at=T0 + timedelta(days=2)),
        attempt("a3", "two-codes", finished_at=T0 + timedelta(days=1)),
    )

    run(monkeypatch, ["1", ""])

    (claim,) = log.claims()
    assert claim.attempt_id == "a2"


def test_the_id_breaks_a_tie_on_the_same_timestamp(tmp_path, monkeypatch, capsys):
    """Same order the drill loop reads a sitting in, so one rule decides
    'latest' wherever the log is grouped."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a3", "two-codes"),
        attempt("a1", "two-codes"),
        attempt("a2", "two-codes"),
    )

    run(monkeypatch, ["1", ""])

    (claim,) = log.claims()
    assert claim.attempt_id == "a3"


def test_an_earlier_attempt_stands_in_when_the_latest_has_no_code(tmp_path, monkeypatch, capsys):
    """The latest *carrying code*: an attempt without code is no evidence, and
    dropping the problem over it would lose a solution that is still readable."""
    log = retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-codes", finished_at=T0),
        attempt("a2", "two-codes", finished_at=T0 + timedelta(days=1), code=None),
    )

    run(monkeypatch, ["1", ""])

    (claim,) = log.claims()
    assert claim.attempt_id == "a1"


def test_a_problem_leaves_the_pool_once_its_attempt_is_claimed(tmp_path, monkeypatch, capsys):
    """Its older attempts are not a second question — offering one would ask
    what a claim already answered."""
    retried(
        tmp_path / "data",
        monkeypatch,
        attempt("a1", "two-codes", finished_at=T0),
        attempt("a2", "two-codes", finished_at=T0 + timedelta(days=1)),
    )

    run(monkeypatch, ["1", ""])
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [])

    assert exit_info.value.code == 0


def seed_many(root, count: int) -> AttemptLog:
    """`count` two-tag problems, an attempt on each — a pool the sample draws
    from, since a problem contributes one attempt however many it holds."""
    log = AttemptLog(root)
    for n in range(count):
        seed_problem(root, id=f"p{n}", techniques=["greedy", "sorting"])
        log.append_attempt(attempt(f"a{n}", f"p{n}"))
    return log


def test_count_caps_how_many_are_asked_about(tmp_path, monkeypatch, capsys):
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    log = seed_many(root, 5)

    run(monkeypatch, ["1", "", "1", ""], "--count", "2")

    assert len(log.claims()) == 2


def test_the_sample_is_spread_across_techniques(tmp_path, monkeypatch, capsys):
    """A pile of one pair of tags does not take the whole sample: the rare
    problem is asked about before a sixth greedy one."""
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    log = seed_many(root, 5)
    seed_problem(root, id="rare", techniques=["backtracking", "trie"])
    log.append_attempt(attempt("a-rare", "rare"))

    run(monkeypatch, ["1", ""], "--count", "1")

    (claim,) = log.claims()
    assert claim.attempt_id == "a-rare"


def test_the_technique_flag_narrows_the_pool(claim_root, monkeypatch, capsys):
    seed_problem(claim_root.root, id="tries", techniques=["sorting", "trie"])
    claim_root.append_attempt(attempt("a3", "tries"))

    run(monkeypatch, ["1", ""], "--technique", "trie", "--count", "1")

    (claim,) = claim_root.claims()
    assert claim.attempt_id == "a3"


def seeded_store(root, monkeypatch) -> AttemptLog:
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    return seed_many(root, 6)


def test_the_same_seed_asks_in_the_same_order(tmp_path, monkeypatch, capsys):
    """Two identical logs, same seed, same sequence — so a sample can be
    described by its seed rather than by listing what it held."""
    first = seeded_store(tmp_path / "one", monkeypatch)
    run(monkeypatch, ["1", "", "1", "", "1", ""], "--count", "3")
    second = seeded_store(tmp_path / "two", monkeypatch)
    run(monkeypatch, ["1", "", "1", "", "1", ""], "--count", "3")

    assert [claim.attempt_id for claim in first.claims()] == [
        claim.attempt_id for claim in second.claims()
    ]


def test_a_claimed_attempt_drops_out_of_the_pool(tmp_path, monkeypatch, capsys):
    """Successive runs make progress rather than re-asking."""
    log = seeded_store(tmp_path / "one", monkeypatch)
    run(monkeypatch, ["1", ""], "--count", "1")
    run(monkeypatch, ["1", ""], "--count", "1")

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
    run(monkeypatch, ["1", ""])

    out = capsys.readouterr().out
    assert "1 greedy" in out
    assert "2 sorting" in out


def test_each_candidate_is_shown_with_its_criterion(claim_root, monkeypatch, capsys):
    """One rulebook and two annotators is what makes their disagreement mean
    something: a reader judging from the code name alone disagrees with the
    classifier over an unclear rule and a different one indistinguishably."""
    run(monkeypatch, ["1", ""])

    out = " ".join(capsys.readouterr().out.split())
    for candidate in ("greedy", "sorting"):
        entry = criteria()[candidate]
        assert " ".join(entry.earns.split()) in out
        assert " ".join(entry.near_miss.split()) in out


def test_a_candidate_carries_its_kind_as_a_test_not_a_label(claim_root, monkeypatch, capsys):
    """The half a bare label drops. A reader who does not already know what a
    kind selects judges a structure on whether it was performed."""
    seed_problem(claim_root.root, id="mixed", techniques=["binary-search-tree", "greedy"])
    claim_root.append_attempt(attempt("a3", "mixed"))

    run(monkeypatch, ["1", ""], "--technique", "binary-search-tree", "--count", "1")

    out = " ".join(capsys.readouterr().out.split())
    assert Kind.PARADIGM.test in out
    assert Kind.STRUCTURE.test in out


def test_the_reader_and_the_classifier_meet_the_same_words(claim_root, monkeypatch, capsys):
    """Wrapping is this reader's, the words are not. Two renderers of one
    rulebook drift, and the drift is invisible in the agreement number."""
    run(monkeypatch, ["1", ""])

    out = " ".join(capsys.readouterr().out.split())
    for candidate in ("greedy", "sorting"):
        for line in criterion(candidate):
            assert " ".join(line.split()) in out


def test_the_criteria_are_shown_in_the_candidates_order(tmp_path, monkeypatch, capsys):
    """The numbers select from the problem's own order. Criteria in vocabulary
    order agree with it only while a problem's codes are stored sorted and the
    vocabulary is alphabetical — neither is a promise to a reader matching rule
    to number."""
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    seed_problem(root, id="unsorted", techniques=["sorting", "greedy"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "unsorted"))

    run(monkeypatch, ["1", ""])

    out = capsys.readouterr().out
    assert "1 sorting   2 greedy" in out
    assert out.index("sorting —") < out.index("greedy —")


def test_a_retired_candidate_costs_its_own_criterion_and_nothing_else(
    tmp_path, monkeypatch, capsys
):
    """Records outlive the vocabulary, so a stored problem can name a code the
    criteria no longer hold. It is still a legal claim."""
    root = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    seed_problem(root, id="retired", techniques=["greedy", "dynamic-programming-2d"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "retired"))

    run(monkeypatch, ["2", ""])

    (claim,) = log.claims()
    assert claim.techniques == ["dynamic-programming-2d"]
    assert criteria()["greedy"].earns in capsys.readouterr().out.replace("\n      ", " ")


def test_revise_shows_a_named_classifier_s_reading_of_the_same_prompt(
    claim_root, monkeypatch, capsys
):
    """The revision pool is what a reading disputes, so the command has to ask
    what each attempt would be sent now — a reading of an older rulebook
    answered a different question and is not a disagreement about this one."""
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    claim_root.append_claim(
        classifier_claim(
            "a1",
            ["sorting"],
            model="claude-opus-5",
            effort="medium",
            prompt_hash=request_hash(["greedy", "sorting"], "def f(): pass"),
            call_id="call-1",
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )

    run(monkeypatch, [""], "--revise", "--model", "claude-opus-5", "--provider", PIN)

    out = capsys.readouterr().out
    assert "1 of 1 disagree" in out
    assert "sorting" in out


def disputing(log, techniques: list[str], *, call_id: str = "call-1") -> None:
    """A reading of a1 at the digest the command asks for, so the revision pool
    holds it."""
    log.append_claim(
        classifier_claim(
            "a1",
            techniques,
            model="claude-opus-5",
            effort="medium",
            prompt_hash=request_hash(["greedy", "sorting"], "def f(): pass"),
            call_id=call_id,
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )


def test_a_revision_records_the_readings_it_was_shown(claim_root, monkeypatch, capsys):
    """`read_as` prints them before the answer, so the claim is no longer
    independent of those configurations. Recorded per call, since the score
    compares configurations and a claim informed by one still measures
    another."""
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    disputing(claim_root, ["sorting"])

    run(monkeypatch, ["2", ""], "--revise", "--model", "claude-opus-5", "--provider", PIN)

    revision = claim_root.claims()[-1]
    assert revision.source is ClaimSource.USER
    assert revision.informed_by == ["call-1"]


def test_a_claim_made_without_the_readings_is_blind(claim_root, monkeypatch, capsys):
    """The ordinary pass shows the code and the candidates and nothing else,
    which is what makes the agreement it is scored on mean anything."""
    run(monkeypatch, ["1", ""])

    (claim,) = claim_root.claims()
    assert claim.informed_by == []


def test_a_reading_of_another_attempt_is_not_recorded(claim_root, monkeypatch, capsys):
    """Only what was in view for this attempt. A configuration that read the
    log but not this one was never shown."""
    seed_problem(claim_root.root, id="other", techniques=["greedy", "sorting"])
    claim_root.append_attempt(attempt("a3", "other"))
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    claim_root.append_claim(user_claim("a3", ["greedy"]))
    disputing(claim_root, ["sorting"])

    run(
        monkeypatch,
        ["2", ""],
        "--revise",
        "--model",
        "claude-opus-5",
        "--provider",
        PIN,
        "--count",
        "1",
    )

    revision = claim_root.claims()[-1]
    assert revision.attempt_id == "a1"
    assert revision.informed_by == ["call-1"]


def test_an_undisputed_attempt_is_offered_for_revision(claim_root, monkeypatch, capsys):
    """Reviewing only what a classifier contests corrects the hand claims in
    one direction: a claim both readers got wrong the same way is never
    revisited, and agreement climbs for reasons unrelated to either being
    right."""
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    disputing(claim_root, ["greedy"])

    run(monkeypatch, [""], "--revise", "--model", "claude-opus-5", "--provider", PIN)

    assert "0 of 1 disagree" in capsys.readouterr().out


def test_the_most_disputed_are_still_asked_about_first(claim_root, monkeypatch, capsys):
    """Offering the agreed ones does not reorder the pool — what decides
    something is still shown before what probably does not."""
    seed_problem(claim_root.root, id="agreed", techniques=["greedy", "sorting"])
    claim_root.append_attempt(attempt("a3", "agreed"))
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    claim_root.append_claim(user_claim("a3", ["greedy"]))
    disputing(claim_root, ["sorting"])
    claim_root.append_claim(
        classifier_claim(
            "a3",
            ["greedy"],
            model="claude-opus-5",
            effort="medium",
            prompt_hash=request_hash(["greedy", "sorting"], "def f(): pass"),
            call_id="call-2",
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )

    run(
        monkeypatch,
        ["", ""],
        "--revise",
        "--model",
        "claude-opus-5",
        "--provider",
        PIN,
        "--count",
        "2",
    )

    out = capsys.readouterr().out
    assert out.index("1 of 1 disagree") < out.index("0 of 1 disagree")


def test_disputed_still_needs_revise(claim_root, monkeypatch, capsys):
    """The flag only means anything beside the readings it filters on. Passing
    it alone is a request the ordinary pass cannot honour, so it is refused
    rather than silently ignored — which the default no longer distinguishes
    by value."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, [], "--disputed", "1")

    assert exit_info.value.code == 2


def test_revise_ignores_a_reading_of_a_prompt_nobody_sends_now(claim_root, monkeypatch, capsys):
    claim_root.append_claim(user_claim("a1", ["greedy"]))
    claim_root.append_claim(
        classifier_claim(
            "a1",
            ["sorting"],
            model="claude-opus-5",
            effort="medium",
            prompt_hash="ffffffffffff",
            call_id="call-1",
            pin=PIN,
            temperature=TEMPERATURE,
        )
    )

    # Asked for disputes specifically: the default pool is every claim, so an
    # ignored reading would leave the attempt in it either way and say nothing.
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            [""],
            "--revise",
            "--model",
            "claude-opus-5",
            "--provider",
            PIN,
            "--disputed",
            "1",
        )

    assert exit_info.value.code == 0
    assert "nothing disputed" in capsys.readouterr().err


def test_zero_records_a_decline(claim_root, monkeypatch, capsys):
    """`0` is an answer: the candidates do not cover what the code did. It is
    the reading the classifier can already record, and adjudication needs the
    user to be able to overturn a claim with it."""
    run(monkeypatch, ["0", ""])

    (claim,) = claim_root.claims()
    assert claim.attempt_id == "a1"
    assert (claim.techniques, claim.declined) == ([], True)
    assert claim.source is ClaimSource.USER


def test_a_skip_still_records_nothing(claim_root, monkeypatch, capsys):
    """The distinction the flag exists for. `s` leaves the attempt unanswered,
    where `0` answers it."""
    run(monkeypatch, ["s", "s"])

    assert claim_root.claims() == []


def test_a_decline_can_supersede_an_earlier_claim(claim_root, monkeypatch, capsys):
    """What the countRangeSum case needs: a hand claim revised to name none of
    the candidates, rather than deleted to get it out of the eval set."""
    claim_root.append_claim(user_claim("a1", ["greedy"]))

    run(monkeypatch, ["0", ""], "--revise")

    latest = standing_claims(claim_root.claims())["a1"]
    assert (latest.techniques, latest.declined) == ([], True)


def test_the_keys_are_announced_before_the_first_prompt(claim_root, monkeypatch, capsys):
    """`0` and `s` are the pair worth spelling out: one is a verdict about the
    code, the other leaves the attempt unanswered. Learning them from the
    retry hint means typing something wrong first."""
    run(monkeypatch, ["1", ""])

    out = capsys.readouterr().out
    assert "0 for none of these" in out
    assert "s skips" in out
