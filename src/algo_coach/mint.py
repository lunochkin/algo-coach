"""Where every stored record is minted, so what one carries is settled in one
place. The id itself is `ids`, which the transport reaches without this module
and the domain it reads."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from algo_coach.ids import new_id
from algo_coach.schema import (
    CallSite,
    CaseResult,
    ClaimSource,
    Confidence,
    Discard,
    Draft,
    DraftCase,
    ExpectedSource,
    FailureMode,
    MachineProvenance,
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
    WritingState,
)
from algo_coach.techniques import is_known


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
    empty unless the caller says otherwise: only a revision has readings in
    view.
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
    written: MachineProvenance,
) -> TechniqueClaim:
    """A claim a model made, naming its configuration whole.

    Membership is checked here because this is the only write path that could
    introduce an unrecognised code; every other draws on the vocabulary
    already. Rejected whole rather than per code, since a claim asserts one
    set.
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
        **written.model_dump(),
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
    written: MachineProvenance,
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
        **written.model_dump(),
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

    The negative is annotated as deliberately as the positive, since the
    machine answers every candidate it was given. `informed_by` is empty unless
    the caller says otherwise.
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
    written: MachineProvenance,
) -> TemplateMatch:
    """One pair a matcher read, positive or negative. The negative is stored,
    or every re-run re-tests every non-match forever, which on a growing corpus
    is nearly every pair."""
    return TemplateMatch(
        id=new_id(),
        created_at=datetime.now(UTC),
        template_id=template_id,
        solution_id=solution_id,
        matched=matched,
        source=MatchSource.CLASSIFIER,
        **written.model_dump(),
    )


def self_label(attempt_id: str, mode: FailureMode) -> SelfLabel:
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)


def generated_problem(
    title: str,
    statement: str,
    *,
    written: MachineProvenance,
    generated_for: str | None = None,
    techniques: Sequence[str] = (),
    difficulty: ProblemDifficulty | None = None,
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
        **written.model_dump(),
    )


def case(
    problem_id: str,
    args: Sequence[Any],
    expected: Any,
    *,
    expected_from: ExpectedSource = ExpectedSource.REFERENCE,
    round: int | None = 0,
    written: MachineProvenance,
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
        **written.model_dump(),
    )


def solution(
    problem_id: str,
    code: str,
    role: SolutionRole,
    *,
    written: MachineProvenance,
) -> Solution:
    """One solution the engine wrote, in the role it was written for. The role
    is passed rather than inferred: both roles pass the same cases, so nothing
    about the code says which this is."""
    return Solution(
        id=new_id(),
        created_at=datetime.now(UTC),
        problem_id=problem_id,
        role=role,
        code=code,
        **written.model_dump(),
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
    written: MachineProvenance,
    problem_id: str | None = None,
    gate: Discard | None = None,
    detail: str = "",
    mutants: int = 0,
    survived: int = 0,
    won: int = 0,
    killed: int = 0,
    rounds: list[int] | None = None,
    offered: int = 0,
    misdeclared: int = 0,
    separating: int | None = None,
    unseparated: str | None = None,
    largest: int | None = None,
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
        killed=killed,
        rounds=list(rounds or []),
        offered=offered,
        misdeclared=misdeclared,
        separating=separating,
        unseparated=unseparated,
        largest=largest,
        **written.model_dump(),
    )


def draft(
    writing_id: str,
    *,
    title: str,
    statement: str,
    canonical: str,
    declared: Sequence[DraftCase],
    difficulty: ProblemDifficulty,
    template_id: str | None = None,
    written: MachineProvenance,
) -> Draft:
    """One attempt at writing a problem, as the generator's call left it.

    The writing id rather than an id of its own: the four site outcomes of this
    attempt already group under it, and a second identity would need a
    reference nothing else carries. The only minter here that is passed its id.
    """
    return Draft(
        id=writing_id,
        state=WritingState.DRAFTED,
        template_id=template_id,
        title=title,
        statement=statement,
        canonical=canonical,
        declared=list(declared),
        difficulty=difficulty,
        generator=written,
    )
