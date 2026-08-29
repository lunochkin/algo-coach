"""Where the engine's identity comes from.

Every stored record carries an id the engine minted and a client never sees.
Kept in one module so the policy is one line to read and one line to change. A
schema model states what a record holds, not where its id came from, and the
clock has no place there either.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from algo_coach.schema import (
    Call,
    CanonicalSolution,
    CaseResult,
    ClaimSource,
    Confidence,
    FailureMode,
    MatchSource,
    Problem,
    ProblemDifficulty,
    SelfLabel,
    TechniqueClaim,
    TemplateMatch,
    TestCase,
    Verification,
)
from algo_coach.techniques import is_known


def new_id() -> str:
    """Opaque and unguessable: nothing may derive one from a record's content,
    or two engines would mint the same id for different attempts."""
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
    """One request to a model, minted where every other id is minted."""
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
    """A claim the user made, in the drill loop or over the stored log. It
    carries no model or prompt version because nothing re-derives it.

    `declined` is how they name none of the candidates. Passed rather than
    inferred from an empty list, so a writer that lost an answer cannot record
    a verdict nobody gave.

    Blind and unsure unless the caller says otherwise: the drill loop asks
    before any classifier has read the attempt, and the hand pass asks from the
    code and the candidates. Only a revision has readings in view, and only it says
    so — a default that guessed would record independence nobody claimed.
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
    """A claim a model made. It names what produced it, since a better
    classifier can recompute it and a user's claim cannot be recomputed at all.

    All of them, never a subset. A reading whose configuration is partly
    unknown cannot be compared with one whose configuration is known. The model
    and effort are copied from the call rather than read through it, so the
    claims file says what produced each claim without opening the call log.

    Membership is checked here because this is the only write path that could
    introduce an unrecognised code. Every other one draws on the vocabulary
    already. Rejected whole rather than
    per code: a claim asserts one set, and writing the half that passed would
    record a set nobody made.
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


def user_match(
    template_id: str,
    problem_id: str,
    *,
    matched: bool,
    informed_by: Sequence[str] = (),
) -> TemplateMatch:
    """One pair the user annotated, positive or negative.

    It carries no configuration because nothing re-derives it. That is what
    makes it the reference a machine reading is scored against, and what makes
    it stand on read however early it was written.

    The negative is annotated as deliberately as the positive. The machine
    answers every candidate of a card, so a reference that only named matches
    would score its "yes" and say nothing about its "no".

    Blind unless the caller says otherwise, as a user claim is. Only an
    annotation asking to see the matcher has a verdict in view, and only it
    records one.
    """
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        problem_id=problem_id,
        matched=matched,
        source=MatchSource.USER,
        informed_by=list(informed_by),
    )


def machine_match(
    template_id: str,
    problem_id: str,
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
    """One pair a matcher read, positive or negative.

    The negative is a record like any other: without it every re-run re-tests
    every non-match forever, which on a growing corpus is nearly all the work.
    The provenance is the claim's, since what a re-run has to know to supersede
    a reading does not change with the question it answers.
    """
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        problem_id=problem_id,
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
    """Only ever the user's — a machine answering the same question produces a
    `Diagnosis`."""
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)


def generated_problem(
    title: str,
    statement: str,
    *,
    generated_for: str,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    techniques: Sequence[str] = (),
    difficulty: ProblemDifficulty | None = None,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> Problem:
    """A problem the engine wrote, and the configuration that wrote it.

    Generated is a problem's only origin, so there is no hand arm to exempt as
    there is for a claim or a match. Provenance is required, and this is the
    one place that supplies it: a call site spelling the fields out could fill
    them partly, and a problem stored that way names a configuration nothing
    can compare it on.

    Sampled rather than greedy, which a reading never is. Generation produces
    an artifact instead of a verdict about one, so no verdict needs protecting
    from variance, and variance is what stops one model's habits becoming the
    whole corpus. The temperature is recorded either way, since a corpus
    written at one is not the corpus written at another.

    The techniques are a view over the problem's canonical solutions, passed
    in rather than read here: the canonical is written in the same act, and
    re-deriving them later is legal.

    `generated_for` names the template the brief asked for. It is what the
    generator knew rather than what a matcher inferred, which is what makes
    the first `TemplateMatch` on the pair provenance. It asserts nothing about
    the templates the problem also exercises.
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


def case(problem_id: str, args: Sequence[Any], expected: Any) -> TestCase:
    """One case of the set a generated problem carries.

    Named `case` rather than `test_case`: pytest collects any callable whose
    name begins with `test_`, so the minter would be run as a test wherever a
    test module imported it.

    Minted here as every stored record is. It carries no provenance: a case is
    not a reading, and the problem it is keyed to already names the
    configuration that wrote both in one call.
    """
    return TestCase(id=new_id(), problem_id=problem_id, args=list(args), expected=expected)


def canonical_solution(
    problem_id: str,
    code: str,
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
    pin: str,
    temperature: float | None = None,
    provider: str | None = None,
    cost: float | None = None,
) -> CanonicalSolution:
    """An exemplary solution, and how each case went against it.

    A machine record like any other, so it names what produced it. Sampled
    rather than greedy, which is why nothing re-derives one: generation makes
    an artifact instead of a verdict, and the variance is what stops one
    model's habits becoming the whole corpus.

    It says nothing about how it ran. Whether the code passes is a fact about
    a run, and `verification` mints the record holding that.
    """
    return CanonicalSolution(
        id=new_id(),
        created_at=datetime.now(UTC),
        problem_id=problem_id,
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
    canonical_id: str,
    *,
    timeout_ms: int,
    results: Sequence[CaseResult] = (),
) -> Verification:
    """One run of a solution against a problem's cases.

    Its own record rather than a field on the solution, because the outcome is
    a fact about the run. The cap and the machine decide a timeout, and a crash
    can come from the runner, so the same code run twice can differ.

    The cap is stored beside the results. Two runs under different caps are not
    comparable, and nothing else would show it.
    """
    return Verification(
        id=new_id(),
        created_at=datetime.now(UTC),
        canonical_id=canonical_id,
        timeout_ms=timeout_ms,
        results=list(results),
    )
