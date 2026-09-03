"""Where every stored record's id and timestamp come from, kept in one module so
the policy is one line to change."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from algo_coach.schema import (
    Call,
    CallSite,
    CaseResult,
    ClaimSource,
    Confidence,
    Discard,
    ExpectedSource,
    FailureMode,
    MatchSource,
    Problem,
    ProblemDifficulty,
    ReadingSource,
    SelfLabel,
    SiteOutcome,
    Solution,
    SolutionRole,
    TechniqueClaim,
    TechniqueReading,
    TemplateMatch,
    TestCase,
    Verification,
)
from algo_coach.techniques import is_known


# Opaque and unguessable: nothing derives an id from a record's content, or two
# engines would mint the same id for different records.
def new_id() -> str:
    return uuid.uuid4().hex


def call(
    *,
    model: str,
    effort: str,
    prompt: str,
    prompt_hash: str,
    response: str | None = None,
    error: str | None = None,
    thinking: str | None = None,
    stop_reason: str | None = None,
    pin: str | None = None,
    temperature: float | None = None,
    provider: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    cost: float | None = None,
    elapsed_ms: int | None = None,
    request_ms: int | None = None,
    attempts: int | None = None,
) -> Call:
    return Call(
        id=new_id(),
        created_at=datetime.now(UTC),
        model=model,
        effort=effort,
        prompt=prompt,
        prompt_hash=prompt_hash,
        response=response,
        error=error,
        thinking=thinking,
        stop_reason=stop_reason,
        pin=pin,
        temperature=temperature,
        provider=provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cost=cost,
        elapsed_ms=elapsed_ms,
        request_ms=request_ms,
        attempts=attempts,
    )


def user_claim(
    attempt_id: str,
    techniques: list[str],
    *,
    confidence: Confidence | None = None,
    informed_by: Sequence[str] = (),
    declined: bool = False,
) -> TechniqueClaim:
    """A claim the user made, carrying no provenance.

    `declined` is passed rather than inferred from an empty list, so a writer
    that lost an answer cannot record a verdict nobody gave. `informed_by` is
    empty unless the caller says otherwise: only a revision has readings in view.
    """
    return TechniqueClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        attempt_id=attempt_id,
        techniques=techniques,
        declined=declined,
        source=ClaimSource.USER,
        informed_by=list(informed_by),
        confidence=confidence,
    )


def classifier_claim(
    attempt_id: str,
    techniques: list[str],
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> TechniqueClaim:
    """A claim a model made, naming its configuration whole.

    Membership is checked here because this is the only write path that could
    introduce an unrecognised code; every other draws on the vocabulary already.
    Rejected whole rather than per code, since a claim asserts one set.
    """
    unknown = [code for code in techniques if not is_known(code)]
    if unknown:
        raise ValueError(f"unknown technique code(s): {', '.join(unknown)}")
    return TechniqueClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        attempt_id=attempt_id,
        techniques=techniques,
        source=ClaimSource.CLASSIFIER,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )


def user_reading(
    solution_id: str,
    techniques: list[str],
    *,
    informed_by: Sequence[str] = (),
) -> TechniqueReading:
    """One solution read by hand, which is what a machine reading is scored
    against. An adjudication rather than testimony: nobody sat for a canonical,
    so this is a verdict on code the user did not produce."""
    return TechniqueReading(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        techniques=techniques,
        source=ReadingSource.USER,
        informed_by=list(informed_by),
    )


def machine_reading(
    solution_id: str,
    techniques: list[str],
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> TechniqueReading:
    """One solution read by a model, naming its configuration whole. Membership
    is checked here as it is on a classifier claim, and rejected whole."""
    unknown = [code for code in techniques if not is_known(code)]
    if unknown:
        raise ValueError(f"unknown technique code(s): {', '.join(unknown)}")
    return TechniqueReading(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        techniques=techniques,
        source=ReadingSource.CLASSIFIER,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )


def user_match(
    template_id: str,
    solution_id: str,
    *,
    matched: bool,
    informed_by: Sequence[str] = (),
) -> TemplateMatch:
    """One pair the user annotated, positive or negative: whether this solution
    displays this form.

    The negative is annotated as deliberately as the positive, since the machine
    answers every candidate it was given. `informed_by` is empty unless the
    caller says otherwise.
    """
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        solution_id=solution_id,
        matched=matched,
        source=MatchSource.USER,
        informed_by=list(informed_by),
    )


def generator_match(template_id: str, solution_id: str) -> TemplateMatch:
    """Provenance rather than a reading, so it carries no configuration."""
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        solution_id=solution_id,
        matched=True,
        source=MatchSource.GENERATOR,
    )


def machine_match(
    template_id: str,
    solution_id: str,
    *,
    matched: bool,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
) -> TemplateMatch:
    """One pair a matcher read, positive or negative. The negative is stored, or
    every re-run re-tests every non-match forever, which on a growing corpus is
    nearly every pair."""
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        solution_id=solution_id,
        matched=matched,
        source=MatchSource.CLASSIFIER,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
    )


def self_label(attempt_id: str, mode: FailureMode) -> SelfLabel:
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)


def generated_problem(
    title: str,
    statement: str,
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    generated_for: str | None = None,
    techniques: Sequence[str] = (),
    difficulty: ProblemDifficulty | None = None,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> Problem:
    """A problem the engine wrote, with its configuration whole.

    The one place that supplies provenance: a call site spelling the fields out
    could fill them partly. The techniques are passed in rather than read here,
    since the canonical is written in the same act. `generated_for` is the
    template the brief asked for, and is absent where the brief named a skill.
    """
    return Problem(
        id=new_id(),
        title=title,
        statement=statement,
        generated_for=generated_for,
        techniques=list(techniques),
        difficulty=difficulty,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )


def case(
    problem_id: str,
    args: Sequence[Any],
    expected: Any,
    *,
    expected_from: ExpectedSource = ExpectedSource.REFERENCE,
    round: int | None = 0,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> TestCase:
    """One case of the set a generated problem carries, and the call that
    proposed its arguments.

    Named `case` rather than `test_case`: pytest collects any callable whose
    name begins with `test_`, and would run the minter as a test. The
    provenance is the proposing call's rather than the problem's: a mutation
    round and the speedup search each write cases at their own configuration.
    `TestCase.expected_from` and `TestCase.round` have no default of their own,
    so any writer that is not this one has to answer.
    """
    return TestCase(
        id=new_id(),
        problem_id=problem_id,
        args=list(args),
        expected=expected,
        expected_from=expected_from,
        round=round,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )


def solution(
    problem_id: str,
    code: str,
    role: SolutionRole,
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> Solution:
    """One solution the engine wrote, in the role it was written for. The role is
    passed rather than inferred: both roles pass the same cases, so nothing about
    the code says which this is."""
    return Solution(
        id=new_id(),
        created_at=datetime.now(UTC),
        problem_id=problem_id,
        role=role,
        code=code,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )


def verification(
    solution_id: str,
    *,
    timeout_ms: int,
    runner: str,
    results: Sequence[CaseResult] = (),
) -> Verification:
    """One run of a solution against a problem's cases, with the cap and the
    runner that decided it."""
    return Verification(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        timeout_ms=timeout_ms,
        runner=runner,
        results=list(results),
    )


def site_outcome(
    site: CallSite,
    writing_id: str,
    template_id: str,
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
    problem_id: str | None = None,
    gate: Discard | None = None,
    detail: str = "",
    mutants: int = 0,
    survived: int = 0,
    won: int = 0,
    separating: int | None = None,
    unseparated: str | None = None,
) -> SiteOutcome:
    """`problem_id` is filled by the caller that lands the problem: a discarded
    draft mints none, and `writing_id` is what groups the four sites either
    way."""
    return SiteOutcome(
        id=new_id(),
        created_at=datetime.now(UTC),
        site=site,
        writing_id=writing_id,
        template_id=template_id,
        problem_id=problem_id,
        gate=gate,
        detail=detail,
        mutants=mutants,
        survived=survived,
        won=won,
        separating=separating,
        unseparated=unseparated,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
        pin=pin,
        temperature=temperature,
        provider=provider,
        cost=cost,
    )
