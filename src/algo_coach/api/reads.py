"""The routes the drill loop reads: the board, the cards, one card as its page
studies it, a technique's candidates, one picked problem, and a sitting's
statement."""

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
    problem_row,
    stalest_first,
    ungrouped,
)
from algo_coach.cards import CardStore
from algo_coach.ladder import Gap, Rung, ladder
from algo_coach.log import (
    AttemptLog,
    CardRunLog,
    RecallLog,
    SittingStore,
    latest_by_attempt,
    latest_recalls,
)
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Card, CardRun, Hint, ProblemDifficulty, RecallAttempt
from algo_coach.sitting import Served, get, serve
from algo_coach.solution_claims import load_problem, load_problems
from algo_coach.solutions import SolutionLog

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


class Picked(BaseModel):
    """The problem a user picked, before its statement is served. The statement
    is left out, as a candidate's is."""

    problem_id: str
    title: str
    difficulty: ProblemDifficulty | None
    techniques: list[str]
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime | None


class Recalled(BaseModel):
    """One template's recall state: the last reproduction of it, and nothing
    of the ones before, which stay in the log."""

    template_id: str
    last_at: datetime | None  # absent where the form was never recalled
    hints: list[Hint]
    verified: bool


class Studied(BaseModel):
    """A card as its page reads it. The ladder, the progress and the recall
    state are folds, and `content.md` gives why none of them is stored."""

    card: Card
    run: CardRun | None  # absent until the card is started
    rungs: list[Rung]
    gaps: list[Gap]
    recall: list[Recalled]


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
def card(root: Root, user_id: UserId, slug: str) -> Studied:
    found = CardStore(root).by_slug(slug)
    if found is None:
        raise HTTPException(status_code=404, detail=f"no card {slug}")
    run = CardRunLog(root).started(user_id, found.id)
    resolved = ladder(
        found,
        load_problems(root),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
        AttemptLog(root).attempts(user_id),
        since=run.started_at if run else None,
    )
    return Studied(
        card=found,
        run=run,
        rungs=resolved.rungs,
        gaps=resolved.gaps,
        recall=_recall(found, RecallLog(root).for_card(user_id, found.id)),
    )


def _recall(card: Card, attempts: list[RecallAttempt]) -> list[Recalled]:
    # a row per template, in the order the card authored them, so a form never
    # recalled reads beside the ones that were
    latest = latest_recalls(attempts)
    return [
        Recalled(
            template_id=template.id,
            last_at=one.created_at if one else None,
            hints=one.hints if one else [],
            verified=bool(one and one.verified),
        )
        for template in card.templates
        for one in [latest.get(template.id)]
    ]


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


# by id alone: a rung of a card's ladder reaches the same problem, and no path
# under a technique names that
@router.get("/problems/{problem_id}")
def picked(root: Root, user_id: UserId, problem_id: str) -> Picked:
    problem = load_problem(root, problem_id)
    if problem is None or not problem.served:
        raise HTTPException(status_code=404, detail=f"no problem {problem_id}")
    attempts = [
        attempt
        for attempt in AttemptLog(root).attempts(user_id)
        if attempt.problem_id == problem_id
    ]
    row = problem_row(problem, attempts)
    return Picked(
        problem_id=problem.id,
        title=problem.title,
        difficulty=problem.difficulty,
        techniques=problem.techniques,
        attempt_count=row.attempt_count,
        solved_count=row.solved_count,
        last_attempt_at=row.last_attempt_at,
    )


# a write, though the loop reads the statement through it: serving mints the
# sitting whose clock starts here
@router.post("/problems/{problem_id}/sittings")
def statement(root: Root, user_id: UserId, problem_id: str) -> Served:
    return serve(ProblemStore(root), SittingStore(root), problem_id, user_id=user_id)


@router.get("/sittings/{sitting_id}")
def sitting(root: Root, user_id: UserId, sitting_id: str) -> Served:
    return get(ProblemStore(root), SittingStore(root), sitting_id, user_id=user_id)
