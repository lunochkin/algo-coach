from collections.abc import Iterable, Mapping

from algo_coach.log import latest_by_attempt
from algo_coach.schema import Attempt, ClaimSource, Problem, TechniqueClaim


def standing_claims(claims: Iterable[TechniqueClaim]) -> dict[str, TechniqueClaim]:
    """The claim that stands for each attempt, keyed by attempt id.

    The user's own if they made one, however late the machine's is; otherwise
    the latest of the classifier's. Latest alone would make the two writers
    race, and the classifier writes far more often — ground truth would last
    until something re-derived over it.

    Which is what makes a machine claim safe to store on an attempt the user
    has claimed: it is a reading, not a candidate. It stays in the log and is
    scored, and never reaches the board.

    `latest_by_attempt` orders within a writer and knows nothing of sources —
    in what order is the log's question, who wins is this record's.
    """
    claims = list(claims)
    return latest_by_attempt(claims) | latest_by_attempt(
        [claim for claim in claims if claim.source is ClaimSource.USER]
    )


def resolve_techniques(
    attempt: Attempt, problem: Problem, claims: Mapping[str, TechniqueClaim]
) -> list[str]:
    """Which techniques an attempt exercised: its claim if one names any,
    otherwise the techniques of the problem it answers.

    A claim naming none is the classifier reporting that the candidates did not
    cover the code. It is stored so the reading is not paid for again, and it
    answers nothing — so the fallback stands, exactly as it did when such a
    verdict went unrecorded.

    `claims` is keyed by attempt id — `standing_claims` over the log.

    Derived on read and never stored, so re-deriving the tag mapping reaches
    every unclaimed attempt. Sorted and deduplicated, as `map_tags` is, so
    grouping does not depend on how a claim ordered its codes.
    """
    claim = claims.get(attempt.id)
    return sorted(set(claim.techniques if claim and claim.techniques else problem.techniques))
