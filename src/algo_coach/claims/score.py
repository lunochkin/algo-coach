"""The classifier scored against the user's own claims.

Per technique rather than overall, since the board is per technique and a
classifier that over-claims one code skews it wherever that code is read.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import classify
from algo_coach.claims.run import Failed
from algo_coach.claims.sample import eligible, recency
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.schema import ClaimSource, Problem


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
    limit: int | None = None,
) -> Score:
    """Classify the hand-claimed attempts and score the verdicts.

    Nothing is written. A machine claim landing on an attempt the user claimed
    would be the later record, and the latest wins on read — the classifier
    would supersede the evidence it is being measured against.
    """
    claimed = latest_by_attempt(log.claims())
    hand_claimed = [
        attempt
        for attempt in sorted(
            eligible(log.attempts(), problems, user_id=user_id), key=recency, reverse=True
        )
        if attempt.id in claimed and claimed[attempt.id].source is ClaimSource.USER
    ]

    truth: dict[str, Sequence[str]] = {}
    machine: dict[str, Sequence[str]] = {}
    failed: list[Failed] = []
    for attempt in hand_claimed[:limit]:
        truth[attempt.id] = claimed[attempt.id].techniques
        try:
            machine[attempt.id] = classify(
                client, problems[attempt.problem_id].techniques, attempt.code or ""
            )
        except Exception as exc:
            # One attempt's problem, as in the backlog run: an eval that dies
            # on the first refusal reports nothing about the rest.
            failed.append(Failed(attempt_id=attempt.id, reason=repr(exc)))

    result = score(truth, machine)
    result.failed = failed
    return result
