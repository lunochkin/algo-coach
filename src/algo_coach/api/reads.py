"""The routes the drill loop's first three steps read: the board, a technique's
cards and candidates, and a problem's statement."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from algo_coach.api.context import Root, UserId
from algo_coach.attempt_claims import standing_attempt_claims
from algo_coach.board import (
    TechniqueRow,
    candidates,
    excluded,
    per_technique,
    stalest_first,
    ungrouped,
)
from algo_coach.cards import CardStore, without_optional
from algo_coach.log import AttemptLog, SittingStore, latest_by_attempt
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Card, ProblemDifficulty
from algo_coach.sitting import Served, get, serve
from algo_coach.solution_claims import load_problems

router = APIRouter()


class Board(BaseModel):
    rows: list[TechniqueRow]
    ungrouped: int
    excluded: int


class Candidate(BaseModel):
    """A problem offered for a drill. The statement is left out: the clock
    starts when it is served."""

    problem_id: str
    title: str
    difficulty: ProblemDifficulty | None
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime | None


@router.get("/board")
def board(root: Root, user_id: UserId) -> Board:
    log = AttemptLog(root)
    attempts = _own(log, user_id)
    problems = {problem.id: problem for problem in load_problems(root)}
    claims = standing_attempt_claims(log.claims())
    rows = per_technique(attempts, problems, claims, latest_by_attempt(log.self_labels()))
    return Board(
        rows=stalest_first(rows, problems.values()),
        ungrouped=len(ungrouped(attempts, problems, claims)),
        excluded=len(excluded(attempts, problems)),
    )


@router.get("/techniques/{technique}/cards")
def cards(root: Root, technique: str) -> list[Card]:
    return [without_optional(card) for card in CardStore(root).for_technique(technique)]


@router.get("/techniques/{technique}/candidates")
def offered(root: Root, user_id: UserId, technique: str) -> list[Candidate]:
    rows = candidates(technique, load_problems(root), _own(AttemptLog(root), user_id))
    return [
        Candidate(
            problem_id=row.problem.id,
            title=row.problem.title,
            difficulty=row.problem.difficulty,
            attempt_count=row.attempt_count,
            solved_count=row.solved_count,
            last_attempt_at=row.last_attempt_at,
        )
        for row in rows
    ]


# a write, though the loop reads the statement through it: serving mints the
# sitting whose clock starts here
@router.post("/problems/{problem_id}/sittings")
def statement(root: Root, user_id: UserId, problem_id: str) -> Served:
    return serve(ProblemStore(root), SittingStore(root), problem_id, user_id=user_id)


@router.get("/sittings/{sitting_id}")
def sitting(root: Root, user_id: UserId, sitting_id: str) -> Served:
    return get(ProblemStore(root), SittingStore(root), sitting_id, user_id=user_id)


def _own(log: AttemptLog, user_id: str) -> list[Attempt]:
    return [attempt for attempt in log.attempts() if attempt.user_id == user_id]
