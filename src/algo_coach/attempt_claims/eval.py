"""Every configuration named over the eval set, in one run: what each read,
what it reused, and how the configurations compare."""

from collections.abc import Callable, Iterator, Mapping, Sequence

from algo_coach.attempt_claims.attribution import standing_attempt_claims
from algo_coach.attempt_claims.plan import Plan, absorb, select
from algo_coach.attempt_claims.run import Progress, read_one
from algo_coach.attempt_claims.sample import answered_by_hand, eligible, one_per_problem
from algo_coach.attempt_claims.score import (
    Comparison,
    ConfigurationScore,
    Split,
    per_decision,
    score,
    spent,
)
from algo_coach.calls import CallLog, Transport
from algo_coach.classifier import DEFAULT
from algo_coach.log import AttemptLog
from algo_coach.runs import CONCURRENCY, as_answered_grouped
from algo_coach.schema import Attempt, Call, Configuration, Problem


def queued(plans: Sequence[Plan]) -> Iterator[tuple[Plan, Attempt]]:
    """One deployment's work, drawn round-robin from the configurations sharing
    it, so none waits for another to finish.

    A generator on purpose: the next item is asked for only after the previous
    answer was folded in, so an aborted plan is already marked when the check
    runs, and an abort costs one configuration rather than the endpoint.
    """
    queues = [(plan, iter(plan.asking)) for plan in plans]
    while queues:
        alive: list[tuple[Plan, Iterator[Attempt]]] = []
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

    The eval set is decided here and the run is not: one attempt per
    problem, and only those the user answered. `standing` and `claims` are read
    once though the run writes as it goes — what it writes is the classifier's,
    and a user's claim wins by source rather than by being the earlier record.
    """
    claims = log.claims()
    standing = standing_attempt_claims(claims)
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
        if transport is None:
            # `--stored` plans nothing to ask, so this is never reached there
            raise ValueError("a classifier run needs a transport")
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

    results = [plan.result for plan in plans]

    common = (
        set[str].intersection(*(set(result.verdicts) for result in results))
        if results
        else set[str]()
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
    for configuration, run in zip(configurations, results, strict=True):
        scored = score(truth, run.verdicts)
        scored.decisions, scored.decisions_agreed = per_decision(truth, run.verdicts, candidates)
        scored.failed = run.failed
        scored.read, scored.reused = run.read, run.reused
        scored.cost, scored.costed = run.cost, run.costed
        spent(scored, [seen[one] for one in run.call_ids if one in seen])
        scored.undecided = run.undecided
        scored.aborted = run.aborted
        result.scores.append(ConfigurationScore(configuration=configuration, score=scored))

    # In eval-set order, which is the order the disagreements print in, so the
    # two lists read against each other.
    for attempt in hand_claimed:
        if attempt.id not in common:
            continue
        verdicts = [sorted(set(run.verdicts[attempt.id])) for run in results]
        if any(verdict != verdicts[0] for verdict in verdicts[1:]):
            result.splits.append(
                Split(
                    attempt_id=attempt.id,
                    user=sorted(set(truth[attempt.id])),
                    verdicts=verdicts,
                )
            )
    return result
