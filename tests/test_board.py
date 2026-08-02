from datetime import UTC, datetime, timedelta

import pytest

from algo_coach.board import TechniqueRow, per_technique, ungrouped
from algo_coach.log import latest_by_attempt
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    FailureMode,
    Problem,
    ProblemOwner,
    SelfLabel,
    TechniqueClaim,
)
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def make_attempt(
    id: str = "a1",
    *,
    problem_id: str = "greedy-problem",
    finished_at: datetime = T0,
    solved: bool = True,
) -> Attempt:
    return Attempt(
        id=id,
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=solved,
        origin=AttemptOrigin.PUSH,
        external_id=f"ext-{id}",
    )


def make_problem(id: str, source_tags: list[str]) -> Problem:
    return Problem(
        id=id,
        external_id=id,
        user_id="u1",
        owner=ProblemOwner.USER,
        title=id,
        title_slug=id,
        source_tags=source_tags,
        techniques=map_tags(source_tags),
    )


def make_claim(techniques: list[str], *, attempt_id: str = "a1") -> TechniqueClaim:
    return TechniqueClaim(
        id=f"c-{attempt_id}",
        created_at=T0,
        attempt_id=attempt_id,
        techniques=techniques,
        source=ClaimSource.USER,
    )


def make_label(
    mode: FailureMode, *, attempt_id: str = "a1", created_at: datetime = T0
) -> SelfLabel:
    return SelfLabel(id=f"l-{attempt_id}", created_at=created_at, attempt_id=attempt_id, mode=mode)


def index(*problems: Problem) -> dict[str, Problem]:
    return {problem.id: problem for problem in problems}


GREEDY = make_problem("greedy-problem", ["Greedy"])


def test_an_empty_log_has_no_rows():
    assert per_technique([], {}, {}, {}) == []


def test_a_row_counts_the_attempts_that_reached_it():
    attempts = [make_attempt("a1"), make_attempt("a2"), make_attempt("a3")]

    (row,) = per_technique(attempts, index(GREEDY), {}, {})

    assert row.technique == "greedy"
    assert row.attempt_count == 3


def test_a_row_splits_solved_from_unsolved():
    attempts = [
        make_attempt("a1", solved=True),
        make_attempt("a2", solved=False),
        make_attempt("a3", solved=False),
    ]

    (row,) = per_technique(attempts, index(GREEDY), {}, {})

    assert (row.solved_count, row.unsolved_count) == (1, 2)


def test_recency_is_the_latest_attempt():
    """Not the latest ingested: a backfill lands out of order."""
    attempts = [
        make_attempt("a1", finished_at=T0 + timedelta(days=2)),
        make_attempt("a2", finished_at=T0),
    ]

    (row,) = per_technique(attempts, index(GREEDY), {}, {})

    assert row.last_attempt_at == T0 + timedelta(days=2)


def test_self_labels_are_counted_per_mode():
    attempts = [make_attempt("a1"), make_attempt("a2"), make_attempt("a3")]
    labels = latest_by_attempt(
        [
            make_label(FailureMode.RUST, attempt_id="a1"),
            make_label(FailureMode.RUST, attempt_id="a2"),
            make_label(FailureMode.GAP, attempt_id="a3"),
        ]
    )

    (row,) = per_technique(attempts, index(GREEDY), {}, labels)

    assert row.self_labels == {FailureMode.RUST: 2, FailureMode.GAP: 1}


def test_an_unlabelled_attempt_counts_toward_the_row_and_no_mode():
    attempts = [make_attempt("a1"), make_attempt("a2")]
    labels = latest_by_attempt([make_label(FailureMode.GAP, attempt_id="a1")])

    (row,) = per_technique(attempts, index(GREEDY), {}, labels)

    assert row.attempt_count == 2
    assert row.self_labels == {FailureMode.GAP: 1}


def test_a_relabelled_attempt_counts_once_under_its_latest_mode():
    """The first verdict stays in the log and must not reach the row."""
    labels = latest_by_attempt(
        [
            make_label(FailureMode.GAP),
            make_label(FailureMode.RUST, created_at=T0 + timedelta(days=1)),
        ]
    )

    (row,) = per_technique([make_attempt("a1")], index(GREEDY), {}, labels)

    assert row.self_labels == {FailureMode.RUST: 1}


def test_an_attempt_counts_once_in_every_technique_it_names():
    """A solution using two techniques is evidence about both. Over-crediting
    is the known cost of fallback attribution, not a bug in the count."""
    problem = make_problem("two-tags", ["Greedy", "Sorting"])

    rows = per_technique([make_attempt("a1", problem_id="two-tags")], index(problem), {}, {})

    assert [(row.technique, row.attempt_count) for row in rows] == [
        ("greedy", 1),
        ("sorting", 1),
    ]


def test_a_claim_moves_an_attempt_to_the_technique_it_claims():
    claims = latest_by_attempt([make_claim(["two-pointers"])])

    rows = per_technique([make_attempt("a1")], index(GREEDY), claims, {})

    assert [row.technique for row in rows] == ["two-pointers"]


def test_an_attempt_resolving_to_no_technique_produces_no_row():
    """An unmapped tag blocks nothing and invents nothing."""
    problem = make_problem("unmapped", ["Brainteaser"])

    assert per_technique([make_attempt("a1", problem_id="unmapped")], index(problem), {}, {}) == []


def test_rows_are_ordered_by_technique_code():
    """Deterministic, so two renders of the same log read the same. Weakness
    ordering belongs to scheduling, not to the view."""
    problem = make_problem("wide", ["Sorting", "Greedy", "Backtracking"])

    rows = per_technique([make_attempt("a1", problem_id="wide")], index(problem), {}, {})

    assert [row.technique for row in rows] == ["backtracking", "greedy", "sorting"]


def test_a_technique_only_a_claim_names_still_gets_a_row():
    """The vocabulary is wider than what the tags of the log happen to reach."""
    claims = latest_by_attempt([make_claim(["binary-search"], attempt_id="a2")])
    attempts = [make_attempt("a1"), make_attempt("a2")]

    rows = per_technique(attempts, index(GREEDY), claims, {})

    assert [row.technique for row in rows] == ["binary-search", "greedy"]


def test_a_problem_reference_that_does_not_resolve_is_an_error():
    """Every reference on an append-only record is engine-minted and resolves;
    a board that quietly dropped one would under-count in silence."""
    with pytest.raises(KeyError):
        per_technique([make_attempt("a1", problem_id="never-ingested")], {}, {}, {})


def test_a_row_is_never_stored():
    """Derived on read: the model has no id and nothing to write it by."""
    assert "id" not in TechniqueRow.model_fields


def test_ungrouped_names_the_attempts_no_row_reached():
    problem = make_problem("unmapped", ["Brainteaser"])
    missed = make_attempt("a1", problem_id="unmapped")

    assert ungrouped([missed, make_attempt("a2")], index(problem, GREEDY), {}) == [missed]


def test_an_attempt_a_claim_rescues_is_not_ungrouped():
    """Its problem maps to nothing, but the claim says what it exercised."""
    problem = make_problem("unmapped", ["Brainteaser"])
    claims = latest_by_attempt([make_claim(["greedy"])])

    assert ungrouped([make_attempt("a1", problem_id="unmapped")], index(problem), claims) == []


def test_ungrouped_and_the_rows_partition_nothing():
    """An attempt on several techniques is on several rows; the two counts
    answer different questions and are not meant to add up."""
    problem = make_problem("two-tags", ["Greedy", "Sorting"])
    attempts = [make_attempt("a1", problem_id="two-tags")]

    rows = per_technique(attempts, index(problem), {}, {})

    assert sum(row.attempt_count for row in rows) == 2
    assert ungrouped(attempts, index(problem), {}) == []
