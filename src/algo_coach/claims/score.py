"""The classifier scored against the user's own claims, per technique."""

from collections.abc import Callable, Iterator, Mapping, Sequence

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.claims.reading import Plan, absorb, select
from algo_coach.claims.run import CONCURRENCY, Failed, Progress, read_one
from algo_coach.claims.sample import answered_by_hand, eligible, one_per_problem
from algo_coach.classifier import DEFAULT
from algo_coach.log import AttemptLog
from algo_coach.runs import as_answered_grouped
from algo_coach.schema import Attempt, Call, Configuration, Problem
from algo_coach.techniques import standing_claims


class TechniqueScore(BaseModel):
    """One technique's row. `over` and `missed` are asymmetric failures: a code
    admitted too readily against one not recognised."""

    technique: str
    attempts: int = 0  # scored attempts the user's claim names it on
    exact: int = 0  # of `attempts`, those the classifier's whole set agreed on
    missed: int = 0  # of `attempts`, those the classifier did not name it on
    over: int = 0  # attempts it was named on that the user's claim did not —
    # counted outside `attempts`, so the two are not a rate over one
    # denominator


class Disagreement(BaseModel):
    """One attempt the two claims read differently. The hand claims are ground
    truth by construction, not by being right, so which is wrong is a reader's
    question."""

    attempt_id: str
    user: list[str]
    machine: list[str]


class Score(BaseModel):
    scored: int = 0
    exact: int = 0
    # One include/exclude call per candidate on each scored attempt. Set
    # equality compounds them, so a run of near misses reads as a far worse
    # classifier than it is.
    decisions: int = 0
    decisions_agreed: int = 0
    # Of `undecided`, those cut short by the token cap rather than declined.
    exhausted: int = 0
    per_technique: list[TechniqueScore] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    failed: list[Failed] = Field(default_factory=list)
    read: int = 0
    reused: int = 0
    undecided: int = 0
    aborted: bool = False
    # A reading stored before the price was recorded carries none, so a column
    # reports the mean over `costed`.
    cost: float = 0.0
    costed: int = 0
    # Joined from the calls: a claim carries no token counts.
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    tokened: int = 0  # readings whose call reported a count
    reasoned: int = 0  # of those, the ones reporting the thinking split
    # The answering request alone, never what the caller waited: the difference
    # is the endpoint's backoff. The slowest sits beside the mean, which hides
    # an occasional stall.
    request_ms: int = 0
    slowest_ms: int = 0
    timed: int = 0


class ConfigurationScore(BaseModel):
    configuration: Configuration
    score: Score


class Split(BaseModel):
    """One attempt the configurations read differently from each other, as
    distinct from a `Disagreement`, which is with the user."""

    attempt_id: str
    user: list[str]
    verdicts: list[list[str]]  # aligned with `Comparison.scores`


class Comparison(BaseModel):
    """What each configuration read the eval set as. `common` is the attempts
    every configuration decided; `eval_set` is what was there to read."""

    eval_set: int = 0
    common: int = 0
    scores: list[ConfigurationScore] = Field(default_factory=list)
    splits: list[Split] = Field(default_factory=list)


def score(truth: Mapping[str, Sequence[str]], machine: Mapping[str, Sequence[str]]) -> Score:
    """Agreement by set equality, attempt by attempt. A verdict naming no
    candidate is scored like any other; an attempt with no verdict at all is
    unscored, since nothing was read."""
    rows: dict[str, TechniqueScore] = {}

    def row(technique: str) -> TechniqueScore:
        return rows.setdefault(technique, TechniqueScore(technique=technique))

    result = Score()
    for attempt_id, expected in truth.items():
        if attempt_id not in machine:
            continue
        wanted, given = set(expected), set(machine[attempt_id])
        agreed = wanted == given
        result.scored += 1
        result.exact += agreed
        if not agreed:
            result.disagreements.append(
                Disagreement(
                    attempt_id=attempt_id,
                    user=sorted(wanted),
                    machine=sorted(given),
                )
            )
        for technique in wanted:
            row(technique).attempts += 1
            row(technique).exact += agreed
            row(technique).missed += technique not in given
        # Counted outside `attempts`, or the code a classifier reaches for
        # wrongly would be the one code the score cannot see.
        for technique in given - wanted:
            row(technique).over += 1

    result.per_technique = [rows[technique] for technique in sorted(rows)]
    return result


def per_decision(
    truth: Mapping[str, Sequence[str]],
    machine: Mapping[str, Sequence[str]],
    candidates: Mapping[str, Sequence[str]],
) -> tuple[int, int]:
    """How many include/exclude calls a classifier got right, and of how many.

    The denominator is the candidates: declining a code correctly is the
    decision set equality never credits. A disagreement counts only where it
    names a candidate, since a stored reading can carry a retired one.
    """
    total = agreed = 0
    for attempt_id, expected in truth.items():
        offered = set(candidates.get(attempt_id, ()))
        if attempt_id not in machine or not offered:
            continue
        total += len(offered)
        agreed += len(offered) - len((set(expected) ^ set(machine[attempt_id])) & offered)
    return total, agreed


def spent(scored: Score, calls: Sequence[Call]) -> None:
    """Counted over the calls that reported, never over the readings. The
    thinking split and the timing each have their own denominator."""
    for call in calls:
        # An empty verdict has two causes and the claim cannot tell them apart,
        # since both name no technique. The call can, so it is counted here.
        scored.exhausted += call.stop_reason == "length"
        if call.request_ms is not None:
            scored.request_ms += call.request_ms
            scored.slowest_ms = max(scored.slowest_ms, call.request_ms)
            scored.timed += 1
        if call.input_tokens is None or call.output_tokens is None:
            continue
        scored.input_tokens += call.input_tokens
        scored.output_tokens += call.output_tokens
        scored.tokened += 1
        if call.reasoning_tokens is not None:
            scored.reasoning_tokens += call.reasoning_tokens
            scored.reasoned += 1


def queued(plans: Sequence[Plan]) -> Iterator[tuple[Plan, Attempt]]:
    """One deployment's work, drawn round-robin from the configurations sharing
    it, so none waits for another to finish.

    A generator on purpose: the next item is asked for only after the previous
    answer was folded in, so an aborted plan is already marked when the check
    runs, and an abort costs one configuration rather than the endpoint.
    """
    queues = [(plan, iter(plan.asking)) for plan in plans]
    while queues:
        alive = []
        for plan, queue in queues:
            if plan.result.aborted:
                continue
            attempt = next(queue, None)
            if attempt is None:
                continue
            yield plan, attempt
            alive.append((plan, queue))
        queues = alive


def score_backlog(
    transport: Transport | None,
    log: AttemptLog,
    calls: CallLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    configurations: Sequence[Configuration] = (DEFAULT,),
    limit: int | None = None,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_plan: Callable[[Sequence[Plan]], None] | None = None,
    on_progress: Callable[[Configuration, Progress], None] | None = None,
) -> Comparison:
    """What each classifier reads the hand-claimed attempts as, scored.

    The eval set is decided here and the reading is not: one attempt per
    problem, and only those the user answered. `standing` and `claims` are read
    once though the run writes as it goes — what it writes is the classifier's,
    and a user's claim wins by source rather than by being the earlier record.
    """
    claims = log.claims()
    standing = standing_claims(claims)
    hand_claimed = [
        attempt
        for attempt in one_per_problem(eligible(log.attempts(), problems, user_id=user_id))
        if answered_by_hand(standing.get(attempt.id))
    ]

    plans = [
        select(
            hand_claimed,
            problems,
            claims=claims,
            configuration=configuration,
            limit=limit,
            fresh=fresh,
        )
        for configuration in configurations
    ]
    # Once, before the first call: a configuration answered entirely from the
    # log asks for nothing and would otherwise never be reported.
    if on_plan is not None:
        on_plan(plans)

    # Grouped by deployment, since that is what meters the requests. Two
    # configurations differing only in effort share one budget.
    streams: dict[tuple[str, str], list[Plan]] = {}
    for plan in plans:
        if plan.asking:
            streams.setdefault(plan.configuration.deployment, []).append(plan)

    def asked(work: tuple[Plan, Attempt]) -> tuple[list[str], Call | None]:
        plan, attempt = work
        return read_one(
            transport,
            calls,
            attempt,
            problems[attempt.problem_id],
            configuration=plan.configuration,
        )

    for (plan, attempt), answer, failure in as_answered_grouped(
        asked,
        {key: queued(group) for key, group in streams.items()},
        concurrency=concurrency,
    ):
        verdict = absorb(log, plan, attempt, answer, failure)
        if on_progress is not None:
            problem = problems[attempt.problem_id]
            on_progress(
                plan.configuration,
                # Counted as answers arrive: with calls in flight a position in
                # the order asked in jumps about.
                Progress(
                    index=plan.answered,
                    total=len(plan.asking),
                    attempt_id=attempt.id,
                    title=problem.title,
                    **verdict,
                ),
            )

    readings = [plan.result for plan in plans]

    common = (
        set.intersection(*(set(reading.verdicts) for reading in readings)) if readings else set()
    )
    # The whole eval set, not the intersection: `score` and `per_decision` both
    # skip an attempt a configuration has no verdict for, so each is measured
    # over what it read. The trade is that two configurations reading different
    # attempts no longer share a denominator; `common` shows where they
    # diverge.
    truth: dict[str, Sequence[str]] = {
        attempt.id: standing[attempt.id].techniques for attempt in hand_claimed
    }

    candidates = {
        attempt.id: problems[attempt.problem_id].techniques
        for attempt in hand_claimed
        if attempt.problem_id in problems
    }

    # Read once, for the whole comparison. The claims carry no token counts, so
    # this is the only place they can come from.
    seen = {call.id: call for call in calls.all()}

    result = Comparison(eval_set=len(hand_claimed), common=len(common))
    for configuration, reading in zip(configurations, readings, strict=True):
        scored = score(truth, reading.verdicts)
        scored.decisions, scored.decisions_agreed = per_decision(
            truth, reading.verdicts, candidates
        )
        scored.failed = reading.failed
        scored.read, scored.reused = reading.read, reading.reused
        scored.cost, scored.costed = reading.cost, reading.costed
        spent(scored, [seen[one] for one in reading.call_ids if one in seen])
        scored.undecided = reading.undecided
        scored.aborted = reading.aborted
        result.scores.append(ConfigurationScore(configuration=configuration, score=scored))

    # In eval-set order, which is the order the disagreements print in, so the
    # two lists read against each other.
    for attempt in hand_claimed:
        if attempt.id not in common:
            continue
        verdicts = [sorted(set(reading.verdicts[attempt.id])) for reading in readings]
        if any(verdict != verdicts[0] for verdict in verdicts[1:]):
            result.splits.append(
                Split(
                    attempt_id=attempt.id,
                    user=sorted(set(truth[attempt.id])),
                    verdicts=verdicts,
                )
            )
    return result
