"""The classifier over the corpus of canonical solutions."""

from collections.abc import Callable, Iterable
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.classifier import DEFAULT, request_hash
from algo_coach.readings.reader import candidates, read_one, store
from algo_coach.readings.stale import outstanding
from algo_coach.readings.store import ReadingLog
from algo_coach.runs import CONCURRENCY, Bounded, as_answered
from algo_coach.schema import Configuration, Solution, SolutionRole


class Failed(BaseModel):
    solution_id: str
    reason: str


class Progress(BaseModel):
    """One canonical, read. Reported as the run goes, since a call per solution
    makes a corpus run minutes long."""

    index: int  # 1-based, over what this run will ask about
    total: int
    solution_id: str
    problem_id: str  # what the solution answers; the title is the caller's lookup
    techniques: list[str] = Field(default_factory=list)  # empty when the reader named none
    reason: str | None = None  # the failure, when there was one


class ReadingResult(BaseModel):
    read: int = 0
    undecided: int = 0  # named no technique; stored, or every re-run re-reads them
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False

    @property
    def written(self) -> int:
        return self.read + self.undecided


def read_corpus(
    transport: Transport,
    log: ReadingLog,
    calls: CallLog,
    solutions: Iterable[Solution],
    *,
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_progress: Callable[[Progress], None] | None = None,
) -> ReadingResult:
    """Read every stored canonical for its techniques, skipping the ones this
    configuration has already read at the current digest.

    References are never read. Readings are appended as they are made, so a run
    resumes where the last stopped. `fresh` asks again where a stored reading
    answers the same prompt, which is what measuring a reader against itself
    needs.
    """
    asking = [one for one in solutions if one.role is SolutionRole.CANONICAL]
    offered = candidates()
    hashes = {one.id: request_hash(offered, one.code) for one in asking}
    if not fresh:
        asking = outstanding(asking, log.readings(), hashes, configuration=configuration)
    asking = asking[:limit]

    def report(index: int, solution: Solution, **verdict: Any) -> None:
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index,
                    total=len(asking),
                    solution_id=solution.id,
                    problem_id=solution.problem_id,
                    **verdict,
                )
            )

    result = ReadingResult()
    answers = Bounded(
        as_answered(
            lambda solution: read_one(transport, calls, solution, configuration=configuration),
            asking,
            concurrency=concurrency,
        )
    )
    for index, solution, answer, failure in answers:
        if failure is not None:
            # Broad on purpose: a refusal or a dropped connection is one
            # solution's problem, and the corpus behind it must still run.
            result.failed.append(Failed(solution_id=solution.id, reason=repr(failure)))
            report(index, solution, reason=repr(failure))
            continue
        techniques, call = answer if answer is not None else ([], None)
        if call is None:
            # Fewer than two candidates were offered, which the whole
            # vocabulary never is; a reading with no configuration is
            # unstorable.
            continue
        store(log, solution.id, techniques, call)
        if techniques:
            result.read += 1
        else:
            result.undecided += 1
        report(index, solution, techniques=techniques)
    result.aborted = answers.aborted
    return result
