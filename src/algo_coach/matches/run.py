"""The matcher over the corpus."""

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.matches.matcher import DEFAULT, candidates, match, request_hash
from algo_coach.matches.questions import Question, outstanding, questions
from algo_coach.matches.store import MatchLog
from algo_coach.mint import machine_match
from algo_coach.runs import ABORT_AFTER, CONCURRENCY, as_answered
from algo_coach.schema import Call, Card, Configuration, MachineProvenance, Problem, Solution


class Failed(BaseModel):
    card_id: str
    solution_id: str
    reason: str


class Progress(BaseModel):
    """One question, answered, reported as the run goes."""

    index: int  # 1-based, over what this run will ask about
    total: int
    card_slug: str
    title: str  # the problem the solution answers
    templates: list[str] = Field(default_factory=list)  # the slugs it matched
    reason: str | None = None  # the failure, when there was one


class MatchResult(BaseModel):
    asked: int = 0  # calls made, one per card and solution
    matched: int = 0  # pairs recorded as exercised
    unmatched: int = 0  # pairs recorded as not; stored, or every re-run re-tests them
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False

    @property
    def written(self) -> int:
        return self.matched + self.unmatched


def read_one(
    transport: Transport,
    calls: CallLog,
    question: Question,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """What one matcher reads one question as, and the call that read it.

    Writes no record, so it is safe to run several at once: the match log keeps
    one writer however many calls are in flight.
    """
    return match(
        transport,
        calls,
        question.card,
        question.problem,
        question.solution,
        configuration=configuration,
    )


def store(log: MatchLog, question: Question, matched: Sequence[str], call: Call) -> int:
    """Append a verdict per template, returning how many were positive.

    Every candidate gets a record, not only the ones named: a negative is a
    reading a later run must not pay for again.
    """
    named = set(matched)
    written = MachineProvenance.of(call)
    for template in candidates(question.card):
        log.append(
            machine_match(
                template.id,
                question.solution.id,
                matched=template.slug in named,
                written=written,
            )
        )
    return len(named)


def match_corpus(
    transport: Transport,
    log: MatchLog,
    calls: CallLog,
    cards: Iterable[Card],
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    *,
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    card_slug: str | None = None,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_progress: Callable[[Progress], None] | None = None,
) -> MatchResult:
    """Test every canonical a card's technique reaches against that card's
    templates, skipping the questions this configuration has already answered.

    `fresh` asks again where a record already answers the same question, which
    is what measuring a matcher against itself needs.
    """
    asking = questions(
        [card for card in cards if card_slug is None or card.slug == card_slug],
        problems,
        solutions,
    )
    hashes = {
        question.key: request_hash(question.card, question.problem, question.solution)
        for question in asking
    }
    if not fresh:
        asking = outstanding(asking, log.matches(), hashes, configuration=configuration)
    asking = asking[:limit]

    def report(index: int, question: Question, **verdict: Any) -> None:
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index,
                    total=len(asking),
                    card_slug=question.card.slug,
                    title=question.problem.title,
                    **verdict,
                )
            )

    result = MatchResult()
    consecutive = 0
    index = 0
    for question, answer, failure in as_answered(
        lambda question: read_one(transport, calls, question, configuration=configuration),
        asking,
        concurrency=concurrency,
    ):
        index += 1
        if failure is not None:
            # Broad on purpose: a refusal or a dropped connection is one
            # question's problem, and the corpus behind it must still run.
            result.failed.append(
                Failed(
                    card_id=question.card.id,
                    solution_id=question.solution.id,
                    reason=repr(failure),
                )
            )
            report(index, question, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                result.aborted = True
                break
            continue
        consecutive = 0
        matched, call = answer if answer is not None else ([], None)
        if call is None:
            # Nothing was asked, so nothing is recorded.
            continue
        result.asked += 1
        positive = store(log, question, matched, call)
        result.matched += positive
        result.unmatched += len(candidates(question.card)) - positive
        report(index, question, templates=matched)
    return result
