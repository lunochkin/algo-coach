"""The classifier scored against the user's own claims.

Per technique rather than overall, since the board is per technique and a
classifier that over-claims one code skews it wherever that code is read.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import DEFAULT, Configuration
from algo_coach.claims.reading import read
from algo_coach.claims.run import Failed, Progress
from algo_coach.claims.sample import answered_by_hand, eligible, one_per_problem
from algo_coach.log import AttemptLog
from algo_coach.schema import Problem
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
    per_technique: list[TechniqueScore] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    failed: list[Failed] = Field(default_factory=list)
    # What the run cost and what it declined to answer. Reported beside the
    # share, since a classifier that declines gets a smaller denominator and a
    # better number for it.
    read: int = 0
    reused: int = 0
    rehashed: int = 0
    undecided: int = 0


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
    the tags, decides nothing, and would pass a metric that only asks whether
    the right code appears. An attempt the classifier produced no verdict for
    is missing evidence, not a disagreement, so it is not scored.

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


def score_backlog(
    client: Any,
    log: AttemptLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    configurations: Sequence[Configuration] = (DEFAULT,),
    limit: int | None = None,
    on_configuration: Callable[[Configuration], None] | None = None,
    on_progress: Callable[[Progress], None] | None = None,
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

    readings = []
    for configuration in configurations:
        if on_configuration is not None:
            on_configuration(configuration)
        readings.append(
            read(
                client,
                log,
                hand_claimed,
                problems,
                claims=claims,
                configuration=configuration,
                limit=limit,
                on_progress=on_progress,
            )
        )

    common = (
        set.intersection(*(set(reading.verdicts) for reading in readings)) if readings else set()
    )
    truth: dict[str, Sequence[str]] = {
        attempt.id: standing[attempt.id].techniques
        for attempt in hand_claimed
        if attempt.id in common
    }

    result = Comparison(eval_set=len(hand_claimed), common=len(common))
    for configuration, reading in zip(configurations, readings, strict=True):
        scored = score(truth, reading.verdicts)
        scored.failed = reading.failed
        scored.read, scored.reused = reading.read, reading.reused
        scored.rehashed, scored.undecided = reading.rehashed, reading.undecided
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
