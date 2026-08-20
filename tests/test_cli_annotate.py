"""The hand annotation prompt: one card's templates against one problem.

The question is the card and the record is the pair, so one answer writes a
row per template — the forms the problem does not exercise included, since a
reference that only named matches would score the matcher's "yes" and say
nothing about its "no".
"""

import pytest
from matching import PROCEDURE, card, problem, seeded, stored, template

from algo_coach import cli
from algo_coach.cards import CardStore
from algo_coach.matches import MatchLog
from algo_coach.mint import machine_match
from algo_coach.schema import MatchSource


@pytest.fixture
def annotate_root(tmp_path, monkeypatch):
    """One card of three forms and two problems its technique reaches, plus a
    second card nothing asks about unless `--card` says so."""
    root = tmp_path / "data"
    seeded(
        root,
        card(
            "backtracking",
            technique="backtracking",
            templates=[template("subsets"), template("permutations"), template("grid-walk")],
        ),
        card(
            "union-find",
            technique="union-find",
            templates=[template("plain-union"), template("weighted-union")],
        ),
    )
    stored(
        root,
        problem("b0", tags=["Backtracking"]),
        problem("b1", tags=["Backtracking"]),
        problem("u0", tags=["Union Find"]),
    )
    monkeypatch.setattr(cli, "DATA_ROOT", root)
    return root


def run(monkeypatch, answers: list[str], *argv: str) -> None:
    scripted = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(scripted))
    monkeypatch.setattr("sys.argv", ["algo-coach", "annotate", *argv])
    cli.main()


def written(root):
    return MatchLog(root).matches()


def by_slug(root):
    """Minted template id to slug, since a record carries the id and a test
    reads the form."""
    return {one.id: one.slug for card in CardStore(root).all() for one in card.templates}


def read_by_matcher(root):
    """A verdict on `subsets` for every backtracking problem, so whichever the
    order draws first has one to show. Seeded on both, or the test passes by
    drawing the problem nothing read."""
    subsets = next(id for id, name in by_slug(root).items() if name == "subsets")
    for problem_id in ("b0", "b1"):
        MatchLog(root).append(
            machine_match(
                subsets,
                problem_id,
                matched=True,
                model="a-matcher",
                effort="medium",
                prompt_hash="h",
                call_id="c",
                pin="p",
            )
        )


def test_one_answer_writes_a_record_per_template(annotate_root, monkeypatch, capsys):
    """The picked forms positive and the rest negative, in one write: reading
    a statement once to judge three forms is what the question is for."""
    run(monkeypatch, ["1"], "--count", "1", "--card", "backtracking")

    slug = by_slug(annotate_root)
    recorded = {slug[one.template_id]: one.matched for one in written(annotate_root)}
    assert recorded == {"subsets": True, "permutations": False, "grid-walk": False}


def test_several_forms_can_be_named(annotate_root, monkeypatch, capsys):
    """Two approaches to one problem is the ordinary case, and it is what lets
    a rung cover a studied template and an optional one at once."""
    run(monkeypatch, ["1,3"], "--count", "1", "--card", "backtracking")

    slug = by_slug(annotate_root)
    recorded = {slug[one.template_id]: one.matched for one in written(annotate_root)}
    assert recorded == {"subsets": True, "permutations": False, "grid-walk": True}


def test_naming_none_is_negatives_not_a_decline(annotate_root, monkeypatch, capsys):
    """A call naming no template asserts that each of them does not match,
    which is a verdict on every pair. The record shape decides that, so the
    prompt has to be able to say it."""
    run(monkeypatch, ["0"], "--count", "1", "--card", "backtracking")

    recorded = written(annotate_root)
    assert len(recorded) == 3
    assert not any(one.matched for one in recorded)


def test_a_hand_record_carries_no_configuration(annotate_root, monkeypatch, capsys):
    """Nothing re-derives it, which is what makes it the reference a reading is
    scored against."""
    run(monkeypatch, ["1"], "--count", "1", "--card", "backtracking")

    one = written(annotate_root)[0]
    assert one.source is MatchSource.USER
    assert (one.model, one.pin, one.prompt_hash, one.call_id) == (None, None, None, None)


def test_a_skip_writes_nothing_and_moves_on(annotate_root, monkeypatch, capsys):
    run(monkeypatch, ["s", "1"], "--count", "2", "--card", "backtracking")

    assert len({one.problem_id for one in written(annotate_root)}) == 1


def test_the_rest_stops_the_sitting(annotate_root, monkeypatch, capsys):
    """`a` ends it, as the claim prompt has it — there is no default here to
    apply to what is left."""
    run(monkeypatch, ["1", "a"], "--count", "2", "--card", "backtracking")

    assert len({one.problem_id for one in written(annotate_root)}) == 1


def test_eof_keeps_what_already_landed(annotate_root, monkeypatch, capsys):
    """The log is append-only either way, so ending early costs nothing that
    was answered."""

    def once(_):
        if not answers:
            raise EOFError
        return answers.pop(0)

    answers = ["1"]
    monkeypatch.setattr("builtins.input", once)
    monkeypatch.setattr("sys.argv", ["algo-coach", "annotate", "--card", "backtracking"])
    cli.main()

    assert len(written(annotate_root)) == 3


def test_the_statement_is_what_is_read(annotate_root, monkeypatch, capsys):
    """Which form a problem exercises is a question about what it asks, so the
    statement is shown rather than the tags."""
    run(monkeypatch, ["0"], "--count", "1", "--card", "backtracking")

    out = capsys.readouterr().out
    assert "Given an array, return ..." in out


def test_each_form_is_offered_by_its_own_cue(annotate_root, monkeypatch, capsys):
    """A template's trigger says which of the technique's forms this is, which
    is exactly what the annotator is deciding."""
    run(monkeypatch, ["0"], "--count", "1", "--card", "backtracking")

    out = capsys.readouterr().out
    assert "the cue for subsets" in out
    assert "the cue for grid-walk" in out


def test_a_procedure_template_is_never_offered(annotate_root, monkeypatch, capsys):
    """A framing procedure is exercised by every problem its technique reaches,
    so a per-problem verdict on it carries no information."""
    root = annotate_root
    seeded(
        root,
        card(
            "monotonic-stack",
            technique="monotonic-stack",
            templates=[template("next-greater"), template("framing", **PROCEDURE)],
        ),
    )
    stored(root, problem("m0", tags=["Monotonic Stack"]))
    run(monkeypatch, ["1"], "--count", "1", "--card", "monotonic-stack")

    slug = by_slug(root)
    assert {slug[one.template_id] for one in written(root)} == {"next-greater"}


def test_the_matcher_is_not_shown_by_default(annotate_root, monkeypatch, capsys):
    """Blind, or the annotation records what it reviewed rather than what it
    read: the first hand pass is what the line gets drawn by."""
    read_by_matcher(annotate_root)
    run(monkeypatch, ["0"], "--count", "1", "--card", "backtracking")

    assert "a-matcher" not in capsys.readouterr().out


def test_the_matcher_is_shown_on_request(annotate_root, monkeypatch, capsys):
    """Asked for by name, as `claim --revise` shows a reading — and what it
    costs is that the answer is no longer independent of it."""
    read_by_matcher(annotate_root)
    run(monkeypatch, ["0"], "--count", "1", "--card", "backtracking", "--verdict")

    out = capsys.readouterr().out
    assert "a-matcher" in out
    assert "yes  subsets" in out


def test_one_card_is_asked_about_alone(annotate_root, monkeypatch, capsys):
    run(monkeypatch, ["0"], "--count", "1", "--card", "union-find")

    slug = by_slug(annotate_root)
    assert {slug[one.template_id] for one in written(annotate_root)} == {
        "plain-union",
        "weighted-union",
    }


def test_an_unseeded_card_is_refused(annotate_root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit:
        run(monkeypatch, [], "--card", "no-such-card")
    assert exit.value.code == 2


def test_nothing_left_to_annotate_says_so(annotate_root, monkeypatch, capsys):
    run(monkeypatch, ["0", "0"], "--card", "union-find")
    with pytest.raises(SystemExit) as exit:
        run(monkeypatch, [], "--card", "union-find")
    assert exit.value.code == 1
