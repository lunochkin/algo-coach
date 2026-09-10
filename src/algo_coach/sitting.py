"""One timed session on one problem: what the drill loop serves, judges and
mints. `log.md` gives what the record holds and why a pause is an interval."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.problems import ProblemStore
from algo_coach.runner import verify
from algo_coach.schema import Attempt, CaseOutcome, Pause, Sitting, severest

# the cap a sitting judges a submission under. The speedup search picks the
# separating size against it, and generation's own cap sits well above it
DRILL_CAP_MS = 2_000


class Served(BaseModel):
    """What a solver is handed: the statement and the clock, and nothing the
    problem was written from."""

    model_config = ConfigDict(frozen=True)

    title: str
    statement: str  # ends on the `solve` signature
    sitting: Sitting


def serve(
    problems: ProblemStore,
    sittings: SittingStore,
    problem_id: str,
    *,
    user_id: str,
) -> Served:
    problem = problems.get(problem_id)
    if problem is None:
        raise ValueError(f"no problem {problem_id}")
    if not problem.served:
        raise ValueError(f"problem {problem_id} is {problem.status}")
    # a refresh or a second tab reaches the clock already running, rather than
    # starting a second one on the same problem
    one = sittings.running(user_id, problem_id)
    if one is None:
        one = mint.sitting(user_id, problem_id)
        sittings.put(one)
    return Served(title=problem.title, statement=problem.statement, sitting=one)


def submit(
    sittings: SittingStore,
    cases: CaseLog,
    log: AttemptLog,
    sitting_id: str,
    code: str,
    *,
    now: datetime | None = None,
) -> Attempt:
    # taken before the run: judging takes seconds the solver did not spend
    at = now or _clock()
    one = _running(sittings, sitting_id)
    if one.paused:
        raise ValueError(f"sitting {sitting_id} is paused")
    results = verify(code, cases.for_problem(one.problem_id), cap_ms=DRILL_CAP_MS)
    solved = severest(result.outcome for result in results) is CaseOutcome.PASSED
    attempt = mint.attempt(one, code, solved=solved, finished_at=at)
    log.append_attempt(attempt)
    return attempt


def pause(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    if one.paused:
        raise ValueError(f"sitting {sitting_id} is already paused")
    return _stored(store, one, pauses=[*one.pauses, Pause(at=now or _clock())])


def resume(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    if not one.paused:
        raise ValueError(f"sitting {sitting_id} is not paused")
    return _stored(store, one, pauses=_closed(one.pauses, now or _clock()))


def end(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    at = now or _clock()
    # a pause the user never resumed covers the time away, and closing it here
    # is what leaves the sitting ended with none open
    return _stored(
        store, one, pauses=_closed(one.pauses, at) if one.paused else one.pauses, ended_at=at
    )


def _running(store: SittingStore, sitting_id: str) -> Sitting:
    one = store.get(sitting_id)
    if one is None:
        raise ValueError(f"no sitting {sitting_id}")
    if one.ended_at is not None:
        raise ValueError(f"sitting {sitting_id} has ended")
    return one


def _closed(pauses: list[Pause], at: datetime) -> list[Pause]:
    return [*pauses[:-1], Pause(at=pauses[-1].at, until=at)]


def _stored(store: SittingStore, one: Sitting, **changes: object) -> Sitting:
    # revalidated rather than copied: `model_copy` would write a record the
    # interval rules never read
    revised = Sitting.model_validate(one.model_dump() | changes)
    store.put(revised)
    return revised


def _clock() -> datetime:
    return datetime.now(UTC)
