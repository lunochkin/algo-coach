"""The routes the rest of the drill loop takes: the submission, the pause, the
end, and the claim asked of each attempt."""

from fastapi import APIRouter
from pydantic import BaseModel

from algo_coach.api.context import Root, UserId
from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.schema import Attempt, AttemptClaim, Confidence, Sitting
from algo_coach.sitting import (
    Submitted,
    claim,
    end,
    owned_attempt,
    pause,
    resume,
    submit,
    unclaimed,
)
from algo_coach.solution_claims import load_problems

router = APIRouter()


class Submission(BaseModel):
    code: str


class Claim(BaseModel):
    techniques: list[str] = []
    confidence: Confidence
    declined: bool = False


@router.post("/sittings/{sitting_id}/submissions")
def submission(root: Root, user_id: UserId, sitting_id: str, body: Submission) -> Submitted:
    return submit(
        SittingStore(root), CaseLog(root), AttemptLog(root), sitting_id, body.code, user_id=user_id
    )


@router.post("/sittings/{sitting_id}/pause")
def paused(root: Root, user_id: UserId, sitting_id: str) -> Sitting:
    return pause(SittingStore(root), sitting_id, user_id=user_id)


@router.post("/sittings/{sitting_id}/resume")
def resumed(root: Root, user_id: UserId, sitting_id: str) -> Sitting:
    return resume(SittingStore(root), sitting_id, user_id=user_id)


@router.post("/sittings/{sitting_id}/end")
def ended(root: Root, user_id: UserId, sitting_id: str) -> Sitting:
    return end(SittingStore(root), sitting_id, user_id=user_id)


@router.get("/sittings/{sitting_id}/unclaimed")
def unanswered(root: Root, user_id: UserId, sitting_id: str) -> list[Attempt]:
    return unclaimed(AttemptLog(root), sitting_id, user_id=user_id)


@router.post("/attempts/{attempt_id}/claims")
def claimed(root: Root, user_id: UserId, attempt_id: str, body: Claim) -> AttemptClaim:
    log = AttemptLog(root)
    attempt = owned_attempt(log, attempt_id, user_id=user_id)
    (problem,) = [one for one in load_problems(root) if one.id == attempt.problem_id]
    return claim(
        log,
        attempt_id,
        body.techniques,
        candidates=problem.techniques,
        user_id=user_id,
        confidence=body.confidence,
        declined=body.declined,
    )
