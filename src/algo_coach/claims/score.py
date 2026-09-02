"""The classifier scored against the user's own claims.

Per technique rather than overall, since the board is per technique and a
classifier that over-claims one code skews it wherever that code is read.
"""

from collections.abc import Callable, Iterator, Mapping, Sequence

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.claims.reading import Plan, absorb, select
from algo_coach.claims.run import CONCURRENCY, Failed, Progress, read_one
from algo_coach.claims.sample import answered_by_hand, eligible, one_per_problem
from algo_coach.classifier import DEFAULT, Configuration
from algo_coach.log import AttemptLog
from algo_coach.runs import as_answered_grouped
from algo_coach.schema import Attempt, Call, Problem
from algo_coach.techniques import standing_claims


class TechniqueScore(BaseModel):
    """One technique's row. `over` and `missed` are the two asymmetric
    failures and want opposite fixes: a code admitted too readily against one
    the classifier does not recognise.
    """

    technique: str
    attempts: int = 0  # scored attempts the user's claim names it on
    exact: int = 0  # of `attempts`, those the classifier's whole set agreed on
    missed: int = 0  # of `attempts`, those the classifier did not name it on
    over: int = 0  # attempts it was named on that the user's claim did not —
    # counted outside `attempts`, so the two are not a rate over one denominator


class Disagreement(BaseModel):
    """One attempt the two claims read differently. Which of them is wrong is
    the reader's to decide: the hand claims are ground truth by construction,
    not by being right, and a later user claim supersedes an earlier one."""

    attempt_id: str
    user: list[str]
    machine: list[str]


class Score(BaseModel):
    scored: int = 0
    exact: int = 0
    # The include/exclude calls behind the sets — one per candidate on each
    # scored attempt. Set equality compounds them: a classifier right on a
    # share of them lands near that share raised to the candidate count, so a
    # run of near-misses on three-candidate attempts reads as a far worse
    # classifier than it is. Reported beside `exact` to tell a configuration
    # that is broadly weak from one that is narrowly wrong.
    decisions: int = 0
    decisions_agreed: int = 0
    # Of `undecided`, those whose reply was cut short by the token cap rather
    # than considered and declined. Reported apart, because how often a reader
    # finds the candidates wanting is the number that bullet is about, and a
    # runaway decoder says nothing about the candidates.
    exhausted: int = 0
    per_technique: list[TechniqueScore] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    failed: list[Failed] = Field(default_factory=list)
    # What the run cost and what it declined to answer. Reported beside the
    # share, since a classifier that declines gets a smaller denominator and a
    # better number for it.
    read: int = 0
    reused: int = 0
    undecided: int = 0
    aborted: bool = False
    # What this configuration's readings cost, and how many of them said. A
    # mean over the second is what a column reports: a reading stored before
    # the price was recorded carries none, and counting it would understate.
    cost: float = 0.0
    costed: int = 0
    # What the readings spent, averaged by the caller. Joined from the calls
    # rather than copied onto the claims: a claim deliberately holds no token
    # counts, and this is the report that wants them.
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    tokened: int = 0  # readings whose call reported a count
    reasoned: int = 0  # of those, the ones reporting the thinking split
    # The answering request on its own, never what the caller waited. The
    # difference between the two is the endpoint's backoff, and a run held
    # behind a cap would otherwise read as a slow model. The slowest is beside
    # the mean because a reader that stalls occasionally is a different problem
    # from one that is uniformly slow, and a mean hides which it is.
    request_ms: int = 0
    slowest_ms: int = 0
    timed: int = 0


class ConfigurationScore(BaseModel):
    configuration: Configuration
    score: Score


class Split(BaseModel):
    """One attempt the configurations read differently from each other.

    Distinct from a disagreement, which is with the user. Where they answered
    alike there is nothing to choose between them, however wrong both are.
    """

    attempt_id: str
    user: list[str]
    verdicts: list[list[str]]  # aligned with `Comparison.scores`


class Comparison(BaseModel):
    """What each configuration read the eval set as, over one denominator.

    `common` is the attempts every configuration decided: one that read fewer —
    capped, or declining more often — shrinks it for all of them, since a share
    over each one's own sample would read as quality. `eval_set` is what was
    there to read, which tells an empty ground truth from an unread one.
    """

    eval_set: int = 0
    common: int = 0
    scores: list[ConfigurationScore] = Field(default_factory=list)
    splits: list[Split] = Field(default_factory=list)


def score(truth: Mapping[str, Sequence[str]], machine: Mapping[str, Sequence[str]]) -> Score:
    """Agreement by set equality, attempt by attempt.

    Equality rather than overlap: a claim naming every candidate agrees with
    the fallback, decides nothing, and would pass a metric that only asks
    whether the right code appears.

    A verdict naming no candidate is scored like any other. It asserts that
    none of them apply, which a claim naming some of them contradicts — and a
    metric that skipped it would pay a classifier to decline, since every
    decline left a smaller denominator behind. An attempt with no verdict at
    all is still missing evidence and still unscored: nothing was read.

    Every disagreement is returned beside the counts. Reviewing them is how a
    mislabelled hand claim is caught — the eval measures agreement, and only a
    reader can say which side of a disagreement was wrong.
    """
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
        # Counted where it was added, so the code a classifier reaches for
        # wrongly is not the one code the score cannot see.
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

    The denominator is the candidates rather than the claims: declining a code
    correctly is a decision the classifier made, and it is the one set equality
    never credits. Computed here rather than in `score`, which is a pure
    function over the two claim mappings and knows nothing of the problems.

    A disagreement is counted only where it names a candidate. A stored reading
    can carry a code the problem's techniques have since stopped offering, and
    an attempt's decisions must not outnumber the choices it offered.
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
    """Fold what the calls behind a reading consumed into its score.

    Counted over the calls that reported, never over the readings: one made
    before a count was recorded says nothing, and treating it as zero would
    understate whichever configuration was read earliest. The thinking split
    and the timing each have a denominator of their own, since a model may
    report the total and not the part spent reasoning, and a call may be timed
    without its tokens being counted.
    """
    for call in calls:
        # An empty verdict has two causes, and only one of them is a reading.
        # The claim cannot tell them apart, since both name no technique — the
        # call can, so the count is taken here.
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
    """One deployment's work, drawn from the configurations sharing it in turn.

    Round-robin rather than one configuration and then the next, so a
    deployment's budget is spread over them and none waits for another to
    finish.

    A plan that has aborted stops being drawn from, which is why this is a
    generator: the driver asks for the next item only after the previous answer
    was folded in, so an abort is already recorded when the check runs. That is
    what makes an abort cost one configuration rather than the endpoint.
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

    Which attempts are the eval set is decided here and the reading is not: one
    per problem, since a retry asks the identical question, and only those the
    user answered, since the hand claims are what a reading is scored against.

    Every configuration is scored against those hand claims, never against
    another — but over the attempts all of them decided, so the shares share a
    denominator. One configuration is the same path: intersecting one set is
    that set, which is what `score` reaches anyway by skipping what went unread.

    Every reading is stored, so what a configuration answered stays readable
    and a later run pays only where it has not read. On the ordinary correction
    path — the backlog run claims, the user corrects — the reading is already
    there and the score costs nothing.

    `standing` is read once though the run writes as it goes: what it writes is
    the classifier's, and a user's claim wins by source rather than by being
    the earlier record. `claims` likewise, since each configuration finds its
    own readings and no two named here are the same one.
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
    # Once, before the first call. A reader needs every total up front, and a
    # configuration answered entirely from the log asks for nothing — reported
    # per configuration as it started, it would never be mentioned at all.
    if on_plan is not None:
        on_plan(plans)

    # Grouped by deployment, since that is what meters the requests. Two
    # configurations differing only in effort share one budget; one model on
    # two endpoints does not.
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
                # Counted as answers arrive rather than taken from the order
                # asked in: with several calls in flight a position in that
                # order jumps about, and what a reader wants is a count that
                # climbs.
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
    # The whole eval set, not the intersection. `score` and `per_decision`
    # both skip an attempt the configuration has no verdict for, so each is
    # measured over what it read. A share printed as `92/98` carries its own
    # denominator, and `common` is reported beside them so a reader can see
    # where they diverge.
    #
    # The trade: two configurations that read different attempts are no longer
    # scored over one denominator, and the harder of two samples reads as the
    # worse classifier. What it buys is that a configuration is never charged
    # for an attempt another one failed on — an aborted or rate-limited run
    # used to shrink the denominator for every column beside it.
    truth: dict[str, Sequence[str]] = {
        attempt.id: standing[attempt.id].techniques for attempt in hand_claimed
    }

    candidates = {
        attempt.id: problems[attempt.problem_id].techniques
        for attempt in hand_claimed
        if attempt.problem_id in problems
    }

    # Read once, for the whole comparison. The claims deliberately carry no
    # token counts, so this is the only place they can come from — and this is
    # a report rather than a path a board renders from.
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

    # In eval-set order, which is by problem — the order the disagreements print
    # in, so the two lists read against each other.
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
