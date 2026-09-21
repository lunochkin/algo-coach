"""The routes the rest of the drill loop takes: the submission, the pause, the
end, the claim and the label asked of each attempt, and the start of a card's
run."""

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from algo_coach.api.context import Root, UserId
from algo_coach.cards import CardStore
from algo_coach.cases import CaseLog
from algo_coach.ladder import start
from algo_coach.log import AttemptLog, CardRunLog, RecallLog, SittingStore
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.recall import reproduce
from algo_coach.schema import (
    AttemptClaim,
    Card,
    CardRun,
    Confidence,
    FailureMode,
    Hint,
    RecallAttempt,
    SelfLabel,
    Sitting,
    Template,
)
from algo_coach.sitting import (
    Asked,
    Submitted,
    claim,
    end,
    get,
    label,
    owned_attempt,
    pause,
    resume,
    submit,
    unclaimed,
)
from algo_coach.solution_claims import load_problems
from algo_coach.solutions import SolutionLog
from algo_coach.storage import Database

router = APIRouter()


class Submission(BaseModel):
    code: str


class Reproduction(BaseModel):
    """What the trainer sends: the form as typed, and the hints taken before
    it ran."""

    code: str
    hints: list[Hint] = []


class Timed(BaseModel):
    """A sitting a pause, a resume or an end moved, with its elapsed time on the
    engine's clock."""

    sitting: Sitting
    elapsed_sec: float


class Unclaimed(BaseModel):
    """The claim a sitting ends on: the attempts no claim answers yet with the
    modes each one's verdict leaves open, and the problem's techniques they are
    answered over."""

    techniques: list[str]
    attempts: list[Asked]


class Claim(BaseModel):
    techniques: list[str] = []
    confidence: Confidence
    declined: bool = False


class Label(BaseModel):
    """The one mode the solver picked. A skipped label sends no request."""

    mode: FailureMode


# by slug, as the card's own route is: a re-seed keeps the slug and the id is
# minted per store
@router.post("/cards/{slug}/runs")
def started(root: Root, user_id: UserId, slug: str) -> CardRun:
    card = CardStore(root).by_slug(slug)
    if card is None:
        raise HTTPException(status_code=404, detail=f"no card {slug}")
    return start(
        CardRunLog(root),
        card,
        load_problems(root),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
        AttemptLog(root).attempts(user_id),
        user_id=user_id,
    )


# by the template's authored slug, as the page's own path is: the trainer names
# the template it asks for and withholds the form alone
@router.post("/cards/{slug}/recall/{template_slug}")
def recalled(
    root: Root, user_id: UserId, slug: str, template_slug: str, body: Reproduction
) -> RecallAttempt:
    card = _card(root, slug)
    return reproduce(
        RecallLog(root),
        card.id,
        _template(card, template_slug),
        body.code,
        body.hints,
        user_id=user_id,
    )


def _card(root: Database, slug: str) -> Card:
    found = CardStore(root).by_slug(slug)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no card {slug}")
    return found


def _template(card: Card, template_slug: str) -> Template:
    found = [one for one in card.templates if one.slug == template_slug]
    if not found:
        raise HTTPException(status_code=404, detail=f"no template {template_slug}")
    return found[0]


@router.post("/sittings/{sitting_id}/submissions")
def submission(root: Root, user_id: UserId, sitting_id: str, body: Submission) -> Submitted:
    return submit(
        SittingStore(root), CaseLog(root), AttemptLog(root), sitting_id, body.code, user_id=user_id
    )


@router.post("/sittings/{sitting_id}/pause")
def paused(root: Root, user_id: UserId, sitting_id: str) -> Timed:
    return _timed(pause, root, sitting_id, user_id)


@router.post("/sittings/{sitting_id}/resume")
def resumed(root: Root, user_id: UserId, sitting_id: str) -> Timed:
    return _timed(resume, root, sitting_id, user_id)


@router.post("/sittings/{sitting_id}/end")
def ended(root: Root, user_id: UserId, sitting_id: str) -> Timed:
    return _timed(end, root, sitting_id, user_id)


@router.get("/sittings/{sitting_id}/unclaimed")
def unanswered(root: Root, user_id: UserId, sitting_id: str) -> Unclaimed:
    one = get(ProblemStore(root), SittingStore(root), sitting_id, user_id=user_id).sitting
    return Unclaimed(
        techniques=_techniques(root, one.problem_id),
        attempts=unclaimed(AttemptLog(root), sitting_id, user_id=user_id),
    )


@router.post("/attempts/{attempt_id}/claims")
def claimed(root: Root, user_id: UserId, attempt_id: str, body: Claim) -> AttemptClaim:
    log = AttemptLog(root)
    attempt = owned_attempt(log, attempt_id, user_id=user_id)
    return claim(
        log,
        attempt_id,
        body.techniques,
        candidates=_techniques(root, attempt.problem_id),
        user_id=user_id,
        confidence=body.confidence,
        declined=body.declined,
    )


@router.post("/attempts/{attempt_id}/labels")
def labelled(root: Root, user_id: UserId, attempt_id: str, body: Label) -> SelfLabel:
    return label(AttemptLog(root), attempt_id, body.mode, user_id=user_id)


def _techniques(root: Database, problem_id: str) -> list[str]:
    # the derived view, which the stored problem does not carry
    (problem,) = [one for one in load_problems(root) if one.id == problem_id]
    return problem.techniques


def _timed(move: Callable[..., Sitting], root: Database, sitting_id: str, user_id: str) -> Timed:
    # one instant for the move and the reading, so a resume reports no time
    # between the two
    at = datetime.now(UTC)
    one = move(SittingStore(root), sitting_id, user_id=user_id, now=at)
    return Timed(sitting=one, elapsed_sec=one.elapsed(at))
