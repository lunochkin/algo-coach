"""The routes the drill loop reads: the board, the cards, a technique's
candidates, and a sitting's statement."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
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
from algo_coach.cards import CardStore
from algo_coach.log import AttemptLog, SittingStore, latest_by_attempt
from algo_coach.problems import ProblemStore
from algo_coach.schema import Card, ProblemDifficulty
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
    attempts = log.attempts(user_id)
    problems = {problem.id: problem for problem in load_problems(root)}
    claims = standing_attempt_claims(log.claims(user_id))
    rows = per_technique(attempts, problems, claims, latest_by_attempt(log.self_labels(user_id)))
    return Board(
        rows=stalest_first(rows, problems.values()),
        ungrouped=len(ungrouped(attempts, problems, claims)),
        excluded=len(excluded(attempts, problems)),
    )


@router.get("/cards")
def every_card(root: Root) -> list[Card]:
    return sorted(CardStore(root).all(), key=lambda one: (one.technique, one.slug))


# by slug: a re-seed keeps the slug and the URL a page links to, where the id
# is minted per store
@router.get("/cards/{slug}")
def card(root: Root, slug: str) -> Card:
    found = CardStore(root).by_slug(slug)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no card {slug}")
    return found


@router.get("/techniques/{technique}/cards")
def cards(root: Root, technique: str) -> list[Card]:
    return CardStore(root).for_technique(technique)


@router.get("/techniques/{technique}/candidates")
def offered(root: Root, user_id: UserId, technique: str) -> list[Candidate]:
    rows = candidates(technique, load_problems(root), AttemptLog(root).attempts(user_id))
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
