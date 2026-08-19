"""The matcher over the corpus: which pairs are asked about, what each answer
writes, and what a second run pays for."""

from datetime import UTC, datetime

from matching import PROCEDURE, FakeTransport, Verdict, card, problem, seeded, stored, template

from algo_coach.calls import CallLog
from algo_coach.matches import (
    DEFAULT,
    Configuration,
    MatchLog,
    Progress,
    match_corpus,
    outstanding,
    questions,
    request_hash,
)
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import MatchSource, TemplateMatch


def run(root, client: FakeTransport, cards=None, problems=None, **kwargs):
    return match_corpus(
        client,
        MatchLog(root),
        CallLog(root),
        cards if cards is not None else seeded(root),
        problems if problems is not None else stored(root, problem("p1", tags=["Sliding Window"])),
        **kwargs,
    )


def test_candidates_are_pre_filtered_by_technique(tmp_path):
    """Or it is every template against every problem for an answer that is
    almost always no."""
    cards = seeded(tmp_path, card(), card("backtracking", technique="backtracking"))
    corpus = stored(
        tmp_path,
        problem("window", tags=["Sliding Window"]),
        problem("search", tags=["Backtracking"]),
        problem("neither", tags=["Database"]),
    )

    asked = questions(cards, corpus)

    assert {(question.card.slug, question.problem.id) for question in asked} == {
        ("sliding-window", "window"),
        ("backtracking", "search"),
    }


def test_a_card_with_nothing_to_ask_asks_nothing(tmp_path):
    cards = seeded(tmp_path, card(templates=[template("framing", **PROCEDURE)]))

    assert questions(cards, stored(tmp_path, problem("p1", tags=["Sliding Window"]))) == []


def test_one_call_per_card_and_a_record_per_pair(tmp_path):
    """The answer is one subset; the records come from it, positive and
    negative alike."""
    client = FakeTransport.answering(Verdict(["longest-valid-window"]))

    result = run(tmp_path, client)

    assert len(client.calls) == 1
    assert (result.asked, result.matched, result.unmatched) == (1, 1, 1)
    records = MatchLog(tmp_path).matches()
    assert sorted(match.matched for match in records) == [False, True]
    assert {match.problem_id for match in records} == {"p1"}


def test_a_record_carries_what_read_it(tmp_path):
    """A re-run has to know what to supersede, and the log has to read without
    opening the calls."""
    run(tmp_path, FakeTransport.answering(Verdict([])))

    (match, *_) = MatchLog(tmp_path).matches()
    (call,) = CallLog(tmp_path).all()
    assert match.source is MatchSource.CLASSIFIER
    assert (match.model, match.effort, match.pin, match.temperature) == (
        DEFAULT.model,
        DEFAULT.effort,
        DEFAULT.pin,
        DEFAULT.temperature,
    )
    assert (match.call_id, match.prompt_hash, match.provider) == (call.id, call.prompt_hash, "fake")


def test_a_second_run_pays_for_nothing(tmp_path):
    """The pairs carrying no record at the current configuration are what
    still needs testing — the rule readings already use."""
    cards, corpus = seeded(tmp_path), stored(tmp_path, problem("p1", tags=["Sliding Window"]))
    run(tmp_path, FakeTransport.answering(Verdict([])), cards, corpus)

    client = FakeTransport.answering()
    result = run(tmp_path, client, cards, corpus)

    assert (client.calls, result.asked) == ([], 0)


def test_a_new_problem_is_the_only_one_re_read(tmp_path):
    cards = seeded(tmp_path)
    run(
        tmp_path,
        FakeTransport.answering(Verdict([])),
        cards,
        stored(tmp_path, problem("p1", tags=["Sliding Window"])),
    )

    grown = stored(tmp_path, problem("p2", tags=["Sliding Window"]))
    client = FakeTransport.answering(Verdict(["fixed-window"]))
    result = run(tmp_path, client, cards, grown)

    assert result.asked == 1
    assert {match.problem_id for match in MatchLog(tmp_path).matches() if match.matched} == {"p2"}


def test_an_edited_template_re_reads_that_card_alone(tmp_path):
    """The digest is of the question, so a card the edit did not touch stays
    answered."""
    cards = seeded(tmp_path, card(), card("backtracking", technique="backtracking"))
    corpus = stored(
        tmp_path,
        problem("window", tags=["Sliding Window"]),
        problem("search", tags=["Backtracking"]),
    )
    run(tmp_path, FakeTransport.answering(Verdict([]), Verdict([])), cards, corpus)

    edited = seeded(
        tmp_path,
        card(templates=[template("longest-valid-window", code="a different form")]),
        card("backtracking", technique="backtracking"),
    )
    client = FakeTransport.answering(Verdict(["longest-valid-window"]))
    result = run(tmp_path, client, edited, corpus)

    assert result.asked == 1
    assert client.calls[0]["content"].count("a different form") == 1


def test_a_reading_at_another_configuration_is_not_an_answer(tmp_path):
    cards, corpus = seeded(tmp_path), stored(tmp_path, problem("p1", tags=["Sliding Window"]))
    run(tmp_path, FakeTransport.answering(Verdict([])), cards, corpus)

    other = Configuration(model="another-model")
    client = FakeTransport.answering(Verdict([]))
    result = run(tmp_path, client, cards, corpus, configuration=other)

    assert result.asked == 1
    assert MatchLog(tmp_path).matches()[-1].model == "another-model"


def test_fresh_asks_again(tmp_path):
    """What measuring a matcher against itself needs."""
    cards, corpus = seeded(tmp_path), stored(tmp_path, problem("p1", tags=["Sliding Window"]))
    run(tmp_path, FakeTransport.answering(Verdict([])), cards, corpus)

    result = run(tmp_path, FakeTransport.answering(Verdict([])), cards, corpus, fresh=True)

    assert result.asked == 1
    assert len(MatchLog(tmp_path).matches()) == 4


def test_a_hand_annotation_is_never_what_a_run_leans_on(tmp_path):
    """It is the reference a machine run is scored against, so it settles
    nothing about what still has to be read."""
    cards, corpus = seeded(tmp_path), stored(tmp_path, problem("p1", tags=["Sliding Window"]))
    hashes = {(cards[0].id, "p1"): request_hash(cards[0], corpus[0])}
    hand = [
        TemplateMatch(
            id=f"m{index}",
            created_at=datetime.now(UTC),
            template_id=template.id,
            problem_id="p1",
            matched=True,
            source=MatchSource.USER,
        )
        for index, template in enumerate(cards[0].templates)
    ]

    assert outstanding(questions(cards, corpus), hand, hashes, configuration=DEFAULT) != []


def test_a_limit_cuts_the_run(tmp_path):
    cards = seeded(tmp_path)
    corpus = stored(
        tmp_path,
        problem("p1", tags=["Sliding Window"]),
        problem("p2", tags=["Sliding Window"]),
    )
    client = FakeTransport.answering(Verdict([]))

    result = run(tmp_path, client, cards, corpus, limit=1)

    assert (result.asked, len(client.calls)) == (1, 1)


def test_a_failure_costs_its_own_pair(tmp_path):
    cards = seeded(tmp_path)
    corpus = stored(
        tmp_path,
        problem("p1", tags=["Sliding Window"]),
        problem("p2", tags=["Sliding Window"]),
    )
    client = FakeTransport.answering(Verdict(error=RuntimeError("rate limit")), Verdict([]))

    result = run(tmp_path, client, cards, corpus)

    assert (result.asked, len(result.failed), result.aborted) == (1, 1, False)
    assert "rate limit" in result.failed[0].reason


def test_a_broken_run_aborts(tmp_path):
    cards = seeded(tmp_path)
    corpus = stored(
        tmp_path,
        *(problem(f"p{index}", tags=["Sliding Window"]) for index in range(ABORT_AFTER + 2)),
    )
    client = FakeTransport.answering(*[Verdict(error=RuntimeError("bad key"))] * (ABORT_AFTER + 2))

    result = run(tmp_path, client, cards, corpus)

    assert (result.aborted, len(client.calls)) == (True, ABORT_AFTER)


def test_progress_is_reported_as_the_run_goes(tmp_path):
    seen: list[Progress] = []
    run(tmp_path, FakeTransport.answering(Verdict(["fixed-window"])), on_progress=seen.append)

    (step,) = seen
    assert (step.index, step.total, step.card_slug, step.templates) == (
        1,
        1,
        "sliding-window",
        ["fixed-window"],
    )


def test_one_card_at_a_time(tmp_path):
    cards = seeded(tmp_path, card(), card("backtracking", technique="backtracking"))
    corpus = stored(
        tmp_path,
        problem("window", tags=["Sliding Window"]),
        problem("search", tags=["Backtracking"]),
    )
    client = FakeTransport.answering(Verdict([]))

    result = run(tmp_path, client, cards, corpus, card_slug="backtracking")

    assert result.asked == 1
    assert {match.problem_id for match in MatchLog(tmp_path).matches()} == {"search"}
