"""The classifier scored against the user's own claims, per technique."""

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field

from algo_coach.claims.run import Failed
from algo_coach.schema import Call, Configuration


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
