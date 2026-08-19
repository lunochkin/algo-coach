"""The matcher over the corpus.

Re-derivation is the normal path here, not an exception: a technique claim
asks about one attempt and the question never changes, where a match is a
template against a corpus that grows with every push.
"""

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.matches.matcher import DEFAULT, Configuration, candidates, match, request_hash
from algo_coach.matches.pairs import Pair, outstanding, pairs
from algo_coach.matches.store import MatchLog
from algo_coach.mint import machine_match
from algo_coach.runs import ABORT_AFTER, CONCURRENCY, as_answered
from algo_coach.schema import Call, Card, Problem


class Failed(BaseModel):
    card_id: str
    problem_id: str
    reason: str


class Progress(BaseModel):
    """One pair, answered. Reported as the run goes: a call per pair makes a
    corpus run minutes long."""

    index: int  # 1-based, over what this run will ask about
    total: int
    card_slug: str
    title: str  # the problem's
    templates: list[str] = Field(default_factory=list)  # the slugs it matched
    reason: str | None = None  # the failure, when there was one


class MatchResult(BaseModel):
    asked: int = 0  # calls made, one per pair
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
    pair: Pair,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """What one matcher reads one pair as, and the call that read it.

    Makes the call and writes no record, so it is safe to run several at once —
    the records are the caller's, and the match log has one writer however many
    calls are in flight.
    """
    return match(transport, calls, pair.card, pair.problem, configuration=configuration)


def store(log: MatchLog, pair: Pair, matched: Sequence[str], call: Call) -> int:
    """Append a verdict per template, returning how many were positive.

    Every candidate gets a record, not only the ones named: the answer is the
    whole subset, so what it says about the rest is that they do not match, and
    that is the reading a later run must not pay for again.
    """
    named = set(matched)
    for template in candidates(pair.card):
        log.append(
            machine_match(
                template.id,
                pair.problem.id,
                matched=template.slug in named,
                model=call.model,
                effort=call.effort,
                prompt_hash=call.prompt_hash,
                call_id=call.id,
                pin=call.pin or "",
                temperature=call.temperature,
                provider=call.provider,
            )
        )
    return len(named)


def match_corpus(
    transport: Transport,
    log: MatchLog,
    calls: CallLog,
    cards: Iterable[Card],
    problems: Iterable[Problem],
    *,
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    card_slug: str | None = None,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_progress: Callable[[Progress], None] | None = None,
) -> MatchResult:
    """Test every problem a card's technique reaches against that card's
    templates, skipping the pairs this configuration has already answered.

    Written after card import and never before: both references are minted, so
    a match cannot exist until the templates do.

    `fresh` asks again where a record already answers the same question, which
    is what measuring a matcher against itself needs. `on_progress` reports as
    the run goes; printing is the caller's.
    """
    asking = pairs(
        [card for card in cards if card_slug is None or card.slug == card_slug], problems
    )
    hashes = {pair.key: request_hash(pair.card, pair.problem) for pair in asking}
    if not fresh:
        asking = outstanding(asking, log.matches(), hashes, configuration=configuration)
    asking = asking[:limit]

    def report(index: int, pair: Pair, **verdict: Any) -> None:
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index,
                    total=len(asking),
                    card_slug=pair.card.slug,
                    title=pair.problem.title,
                    **verdict,
                )
            )

    result = MatchResult()
    consecutive = 0
    index = 0
    for pair, answer, failure in as_answered(
        lambda pair: read_one(transport, calls, pair, configuration=configuration),
        asking,
        concurrency=concurrency,
    ):
        index += 1
        if failure is not None:
            # Broad on purpose: a refusal, a rate limit or a dropped connection
            # is one pair's problem, and the corpus behind it must still run.
            result.failed.append(
                Failed(card_id=pair.card.id, problem_id=pair.problem.id, reason=repr(failure))
            )
            report(index, pair, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                result.aborted = True
                break
            continue
        consecutive = 0
        matched, call = answer if answer is not None else ([], None)
        if call is None:
            # Nothing was asked, so nothing is recorded: a card of framing
            # procedures alone has no per-problem verdict to give.
            continue
        result.asked += 1
        positive = store(log, pair, matched, call)
        result.matched += positive
        result.unmatched += len(candidates(pair.card)) - positive
        report(index, pair, templates=matched)
    return result
