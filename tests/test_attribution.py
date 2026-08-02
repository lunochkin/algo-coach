from datetime import UTC, datetime, timedelta

from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    Problem,
    ProblemOwner,
    TechniqueClaim,
)
from algo_coach.techniques import map_tags, resolve_techniques

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def make_attempt(id: str = "a1", problem_id: str = "minted-u1") -> Attempt:
    return Attempt(
        id=id,
        user_id="u1",
        problem_id=problem_id,
        finished_at=T0,
        solved=True,
        origin=AttemptOrigin.PUSH,
        external_id=f"ext-{id}",
    )


def make_problem(*, source_tags: list[str] | None = None, id: str = "minted-u1") -> Problem:
    tags = source_tags or []
    return Problem(
        id=id,
        external_id="p1",
        user_id="u1",
        owner=ProblemOwner.USER,
        title="Two Sum",
        title_slug="two-sum",
        source_tags=tags,
        techniques=map_tags(tags),
    )


def make_claim(
    techniques: list[str],
    *,
    id: str = "c1",
    attempt_id: str = "a1",
    created_at: datetime = T0,
    source: ClaimSource = ClaimSource.USER,
) -> TechniqueClaim:
    machine = source is ClaimSource.CLASSIFIER
    return TechniqueClaim(
        id=id,
        created_at=created_at,
        attempt_id=attempt_id,
        techniques=techniques,
        source=source,
        model="m1" if machine else None,
        prompt_version="v1" if machine else None,
    )


def test_an_unclaimed_attempt_falls_back_to_the_problems_techniques():
    """Nothing has to be labelled for an attempt to count — that is what makes
    a backfilled history usable."""
    problem = make_problem(source_tags=["Hash Table", "Greedy"])

    assert resolve_techniques(make_attempt(), problem, {}) == ["greedy", "hashing"]


def test_a_claim_wins_over_the_problems_tags():
    """A tag says what a problem could exercise, a claim what the solution
    did."""
    problem = make_problem(source_tags=["Hash Table", "Sorting"])
    claims = latest_by_attempt([make_claim(["two-pointers"])])

    assert resolve_techniques(make_attempt(), problem, claims) == ["two-pointers"]


def test_a_later_claim_replaces_the_whole_set():
    """Not merged with the earlier one: the earlier record still says
    "dynamic-programming" and must not reach a reader."""
    claims = latest_by_attempt(
        [
            make_claim(["dynamic-programming", "greedy"], id="c1", created_at=T0),
            make_claim(["greedy"], id="c2", created_at=T0 + timedelta(hours=1)),
        ]
    )

    assert resolve_techniques(make_attempt(), make_problem(), claims) == ["greedy"]


def test_the_earlier_claim_never_wins_on_input_order():
    """The log is append-only, but a reader may hand them over sorted any way."""
    late = make_claim(["greedy"], id="c2", created_at=T0 + timedelta(hours=1))
    early = make_claim(["backtracking"], id="c1", created_at=T0)

    assert latest_by_attempt([late, early])["a1"].techniques == ["greedy"]


def test_a_tie_on_created_at_is_broken_by_append_order():
    """Two claims minted in the same instant: the one that landed last stands."""
    claims = latest_by_attempt(
        [
            make_claim(["backtracking"], id="c1"),
            make_claim(["recursion"], id="c2"),
        ]
    )

    assert claims["a1"].techniques == ["recursion"]


def test_a_user_claim_and_a_machine_claim_are_ordered_only_by_time():
    """Both count the same toward progress; recency decides, not the source."""
    claims = latest_by_attempt(
        [
            make_claim(["greedy"], id="c1", created_at=T0, source=ClaimSource.USER),
            make_claim(
                ["dynamic-programming"],
                id="c2",
                created_at=T0 + timedelta(hours=1),
                source=ClaimSource.CLASSIFIER,
            ),
        ]
    )

    assert resolve_techniques(make_attempt(), make_problem(), claims) == ["dynamic-programming"]


def test_a_claim_on_another_attempt_does_not_leak():
    problem = make_problem(source_tags=["Greedy"])
    claims = latest_by_attempt([make_claim(["two-pointers"], attempt_id="a2")])

    assert resolve_techniques(make_attempt("a1"), problem, claims) == ["greedy"]


def test_an_unclaimed_attempt_on_an_unmapped_problem_resolves_to_nothing():
    """An unmapped tag blocks nothing: the attempt simply groups nowhere."""
    problem = make_problem(source_tags=["Brainteaser"])

    assert resolve_techniques(make_attempt(), problem, {}) == []


def test_a_resolved_claim_is_sorted_and_deduplicated():
    """Same shape as `map_tags`, so grouping does not depend on claim order."""
    claims = latest_by_attempt([make_claim(["greedy", "backtracking", "greedy"])])

    assert resolve_techniques(make_attempt(), make_problem(), claims) == [
        "backtracking",
        "greedy",
    ]


def test_re_deriving_the_mapping_reaches_every_unclaimed_attempt():
    """Resolution is read-time, so a mapping change shows up on attempts that
    were ingested before it — and stops at the claimed ones."""
    attempt = make_attempt()
    before = make_problem(source_tags=["Greedy"])
    after = make_problem(source_tags=["Greedy", "Sorting"])

    assert resolve_techniques(attempt, before, {}) == ["greedy"]
    assert resolve_techniques(attempt, after, {}) == ["greedy", "sorting"]

    claims = latest_by_attempt([make_claim(["two-pointers"])])
    assert resolve_techniques(attempt, after, claims) == ["two-pointers"]


def test_resolution_is_never_stored_on_an_attempt():
    """A copy taken at ingest would drift, with no way to tell which is right."""
    assert "techniques" not in Attempt.model_fields


def test_claims_read_back_in_append_order(tmp_path):
    log = AttemptLog(tmp_path)
    first = make_claim(["greedy"], id="c1")
    second = make_claim(["recursion"], id="c2")
    log.append_claim(first)
    log.append_claim(second)

    assert log.claims() == [first, second]


def test_resolving_an_empty_log(tmp_path):
    log = AttemptLog(tmp_path)

    assert latest_by_attempt(log.claims()) == {}
