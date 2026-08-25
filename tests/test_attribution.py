from datetime import UTC, datetime, timedelta

from algo_coach.log import AttemptLog
from algo_coach.schema import (
    Attempt,
    AttemptOrigin,
    ClaimSource,
    Problem,
    ProblemOwner,
    TechniqueClaim,
)
from algo_coach.techniques import resolve_techniques, standing_claims

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


def make_problem(*, techniques: list[str] | None = None, id: str = "minted-u1") -> Problem:
    return Problem(
        id=id,
        external_id="p1",
        user_id="u1",
        owner=ProblemOwner.USER,
        title="Two Sum",
        title_slug="two-sum",
        statement="Given an array, return ...",
        techniques=techniques or [],
    )


def make_claim(
    techniques: list[str],
    *,
    id: str = "c1",
    attempt_id: str = "a1",
    created_at: datetime = T0,
    source: ClaimSource = ClaimSource.USER,
    declined: bool = False,
) -> TechniqueClaim:
    machine = source is ClaimSource.CLASSIFIER
    return TechniqueClaim(
        id=id,
        created_at=created_at,
        attempt_id=attempt_id,
        techniques=techniques,
        source=source,
        declined=declined,
        model="m1" if machine else None,
        effort="medium" if machine else None,
        pin="a-host" if machine else None,
        call_id="call-1" if machine else None,
        prompt_hash="0123456789ab" if machine else None,
    )


def test_an_unclaimed_attempt_falls_back_to_the_problems_techniques():
    """Nothing has to be labelled for an attempt to count — that is what makes
    a backfilled history usable."""
    problem = make_problem(techniques=["greedy", "hashing"])

    assert resolve_techniques(make_attempt(), problem, {}) == ["greedy", "hashing"]


def test_a_claim_wins_over_the_problems_tags():
    """A tag says what a problem could exercise, a claim what the solution
    did."""
    problem = make_problem(techniques=["hashing", "sorting"])
    claims = standing_claims([make_claim(["two-pointers"])])

    assert resolve_techniques(make_attempt(), problem, claims) == ["two-pointers"]


def test_a_later_claim_replaces_the_whole_set():
    """Not merged with the earlier one: the earlier record still says
    "dynamic-programming" and must not reach a reader."""
    claims = standing_claims(
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

    assert standing_claims([late, early])["a1"].techniques == ["greedy"]


def test_a_tie_on_created_at_is_broken_by_append_order():
    """Two claims minted in the same instant: the one that landed last stands."""
    claims = standing_claims(
        [
            make_claim(["backtracking"], id="c1"),
            make_claim(["recursion"], id="c2"),
        ]
    )

    assert claims["a1"].techniques == ["recursion"]


def test_a_later_machine_claim_does_not_supersede_the_users():
    """The classifier writes far more often than the user, so latest alone
    would make ground truth last until something re-derived over it."""
    claims = standing_claims(
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

    assert resolve_techniques(make_attempt(), make_problem(), claims) == ["greedy"]


def test_the_users_claim_stands_over_an_earlier_machine_one_too():
    """The rule is whose, not when: a user claim correcting the classifier and
    one the classifier later read over resolve the same way."""
    claims = standing_claims(
        [
            make_claim(
                ["dynamic-programming"],
                id="c1",
                created_at=T0,
                source=ClaimSource.CLASSIFIER,
            ),
            make_claim(
                ["greedy"], id="c2", created_at=T0 + timedelta(hours=1), source=ClaimSource.USER
            ),
        ]
    )

    assert resolve_techniques(make_attempt(), make_problem(), claims) == ["greedy"]


def test_a_machine_claim_stands_where_no_hand_reached():
    """What the classifier is for: the board reads its claims wherever the
    user made none."""
    claims = standing_claims([make_claim(["sorting"], id="c1", source=ClaimSource.CLASSIFIER)])

    assert resolve_techniques(make_attempt(), make_problem(), claims) == ["sorting"]


def test_the_latest_machine_claim_stands_among_machine_claims():
    """A re-derivation supersedes the reading it replaces, as before — the
    user-first rule orders one writer against the other, not within one."""
    claims = standing_claims(
        [
            make_claim(
                ["dynamic-programming"], id="c1", created_at=T0, source=ClaimSource.CLASSIFIER
            ),
            make_claim(
                ["greedy"],
                id="c2",
                created_at=T0 + timedelta(hours=1),
                source=ClaimSource.CLASSIFIER,
            ),
        ]
    )

    assert claims["a1"].techniques == ["greedy"]


def test_a_superseded_machine_claim_never_resurfaces_on_another_attempt():
    """Each attempt is resolved on its own: a user claim on one does not
    shadow the machine's on the next."""
    claims = standing_claims(
        [
            make_claim(["sorting"], id="c1", attempt_id="a1", source=ClaimSource.CLASSIFIER),
            make_claim(["greedy"], id="c2", attempt_id="a1", source=ClaimSource.USER),
            make_claim(["two-pointers"], id="c3", attempt_id="a2", source=ClaimSource.CLASSIFIER),
        ]
    )

    assert claims["a1"].techniques == ["greedy"]
    assert claims["a2"].techniques == ["two-pointers"]


def test_a_machine_claim_on_a_hand_claimed_attempt_is_kept_in_the_log(tmp_path):
    """A reading, not a candidate: it never reaches the board and never leaves
    the log, which is what makes it safe to store and scoreable later."""
    log = AttemptLog(tmp_path)
    hand = make_claim(["greedy"], id="c1", source=ClaimSource.USER)
    reading = make_claim(
        ["dynamic-programming"],
        id="c2",
        created_at=T0 + timedelta(hours=1),
        source=ClaimSource.CLASSIFIER,
    )
    log.append_claim(hand)
    log.append_claim(reading)

    assert log.claims() == [hand, reading]
    assert standing_claims(log.claims())["a1"] == hand


def test_the_rule_holds_over_a_stream_read_once():
    """A reader that iterated twice would see the second pass empty and hand
    the machine the attempt — silently, since there is nothing to raise on.
    Every caller passes a list today, so nothing else would catch it."""
    hand = make_claim(["greedy"], id="c1", created_at=T0, source=ClaimSource.USER)
    reading = make_claim(
        ["dynamic-programming"],
        id="c2",
        created_at=T0 + timedelta(hours=1),
        source=ClaimSource.CLASSIFIER,
    )

    claims = standing_claims(claim for claim in [hand, reading])

    assert claims["a1"] == hand


def test_a_claim_on_another_attempt_does_not_leak():
    problem = make_problem(techniques=["greedy"])
    claims = standing_claims([make_claim(["two-pointers"], attempt_id="a2")])

    assert resolve_techniques(make_attempt("a1"), problem, claims) == ["greedy"]


def test_an_unclaimed_attempt_on_an_unmapped_problem_resolves_to_nothing():
    """An unmapped tag blocks nothing: the attempt simply groups nowhere."""
    problem = make_problem(techniques=[])

    assert resolve_techniques(make_attempt(), problem, {}) == []


def test_a_resolved_claim_is_sorted_and_deduplicated():
    """Sorted, so grouping does not depend on claim order."""
    claims = standing_claims([make_claim(["greedy", "backtracking", "greedy"])])

    assert resolve_techniques(make_attempt(), make_problem(), claims) == [
        "backtracking",
        "greedy",
    ]


def test_re_deriving_the_mapping_reaches_every_unclaimed_attempt():
    """Resolution is read-time, so a mapping change shows up on attempts that
    were ingested before it — and stops at the claimed ones."""
    attempt = make_attempt()
    before = make_problem(techniques=["greedy"])
    after = make_problem(techniques=["greedy", "sorting"])

    assert resolve_techniques(attempt, before, {}) == ["greedy"]
    assert resolve_techniques(attempt, after, {}) == ["greedy", "sorting"]

    claims = standing_claims([make_claim(["two-pointers"])])
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

    assert standing_claims(log.claims()) == {}


def test_a_user_decline_leaves_the_fallback_standing():
    """The resolver reads a claim's techniques rather than its existence, so a
    decline answers nothing and the tags keep answering — the same rule a
    machine decline already follows, and the board does not move."""
    attempt = make_attempt()
    problem = make_problem(techniques=["greedy", "sorting"])
    claims = standing_claims([make_claim([], declined=True)])

    assert resolve_techniques(attempt, problem, claims) == ["greedy", "sorting"]


def test_a_user_decline_stands_over_a_later_machine_claim():
    """A decline is the user's answer, so it wins on read like any other. The
    machine's stays in the log as a reading and is scored against it."""
    later = make_claim(
        ["greedy"], id="c2", created_at=T0 + timedelta(days=1), source=ClaimSource.CLASSIFIER
    )
    standing = standing_claims([make_claim([], id="c1", declined=True), later])

    assert standing["a1"].id == "c1"
    assert standing["a1"].declined is True
