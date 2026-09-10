"""Where every stored record is minted, so what one carries is settled in one
place. The id itself is `ids`, which the transport reaches without this module
and the domain it reads."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from algo_coach.ids import new_id
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    CallSite,
    CaseResult,
    ClaimSource,
    Confidence,
    Draft,
    DraftCase,
    ExpectedSource,
    FailureMode,
    Gate,
    Json,
    MachineProvenance,
    MatchSource,
    Problem,
    ProblemDifficulty,
    SelfLabel,
    SiteOutcome,
    Sitting,
    Solution,
    SolutionClaim,
    SolutionRole,
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
) -> AttemptClaim:
    """A claim the user made, carrying no provenance.

    `declined` is passed rather than inferred from an empty list, so a writer
    that lost an answer cannot record a verdict nobody gave. `informed_by` is
    empty unless the caller says otherwise: only a revision has machine claims in
    view.
    """
    return AttemptClaim(
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
    provenance: MachineProvenance,
) -> AttemptClaim:
    """A claim a model made, naming its configuration whole.

    Membership is checked here because this is the only write path that could
    introduce an unrecognised code; every other draws on the vocabulary
    already. Rejected whole rather than per code, since a claim asserts one
    set.
    """
    unknown = [code for code in techniques if not is_known(code)]
    if unknown:
        raise ValueError(f"unknown technique code(s): {', '.join(unknown)}")
    return AttemptClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        attempt_id=attempt_id,
        techniques=techniques,
        source=ClaimSource.CLASSIFIER,
        **provenance.model_dump(),
    )


def user_solution_claim(
    solution_id: str,
    techniques: list[str],
    *,
    informed_by: Sequence[str] = (),
) -> SolutionClaim:
    """One solution read by hand, which is what a machine solution claim is scored
    against. An adjudication rather than testimony: nobody sat for a canonical,
    so this is a verdict on code the user did not produce."""
    return SolutionClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        techniques=techniques,
        source=ClaimSource.USER,
        informed_by=list(informed_by),
    )


def machine_solution_claim(
    solution_id: str,
    techniques: list[str],
    *,
    provenance: MachineProvenance,
) -> SolutionClaim:
    """One solution read by a model, naming its configuration whole. Membership
    is checked here as it is on a classifier claim, and rejected whole."""
    unknown = [code for code in techniques if not is_known(code)]
    if unknown:
        raise ValueError(f"unknown technique code(s): {', '.join(unknown)}")
    return SolutionClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        techniques=techniques,
        source=ClaimSource.CLASSIFIER,
        **provenance.model_dump(),
    )


def user_match(
    template_id: str,
    solution_id: str,
    *,
    matched: bool,
    informed_by: Sequence[str] = (),
) -> TemplateMatch:
    """One pair the user matched by hand, positive or negative: whether this solution
    displays this form.

    The negative is recorded as deliberately as the positive, since the
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
    """Provenance rather than an inference, so it carries no configuration."""
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
    provenance: MachineProvenance,
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
        **provenance.model_dump(),
    )


def self_label(attempt_id: str, mode: FailureMode) -> SelfLabel:
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)


def attempt(sitting: Sitting, code: str, *, solved: bool, finished_at: datetime) -> Attempt:
    return Attempt(
        id=new_id(),
        user_id=sitting.user_id,
        problem_id=sitting.problem_id,
        sitting_id=sitting.id,
        started_at=sitting.started_at,
        finished_at=finished_at,
        language="python",
        # cumulative and with every pause excluded: `log.md` gives why
        time_to_solve_sec=sitting.elapsed(finished_at),
        solved=solved,
        code=code,
    )


def sitting(user_id: str, problem_id: str) -> Sitting:
    return Sitting(
        id=new_id(),
        user_id=user_id,
        problem_id=problem_id,
        started_at=datetime.now(UTC),
    )


def generated_problem(
    title: str,
    statement: str,
    *,
    provenance: MachineProvenance,
    target_template_id: str | None = None,
    target_technique: str | None = None,
    techniques: Sequence[str] = (),
    difficulty: ProblemDifficulty | None = None,
) -> Problem:
    """A problem the engine wrote, with its configuration whole.

    The one place that supplies provenance: a call site spelling the fields out
    could fill them partly. The techniques are passed in rather than read here,
    since the canonical is written in the same act. The target is one of the
    two, by the kind it named.
    """
    return Problem(
        id=new_id(),
        title=title,
        statement=statement,
        target_template_id=target_template_id,
        target_technique=target_technique,
        techniques=list(techniques),
        difficulty=difficulty,
        **provenance.model_dump(),
    )


def case(
    problem_id: str,
    args: Sequence[Any],
    expected: Json,
    *,
    expected_from: ExpectedSource = ExpectedSource.REFERENCE,
    round: int | None = 0,
    repeats: int = 1,
    provenance: MachineProvenance,
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
        repeats=repeats,
        **provenance.model_dump(),
    )


def solution(
    problem_id: str,
    code: str,
    role: SolutionRole,
    *,
    provenance: MachineProvenance,
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
        **provenance.model_dump(),
    )


def verification(
    solution_id: str,
    *,
    cap_ms: int,
    runner: str,
    results: Sequence[CaseResult] = (),
) -> Verification:
    """One run of a solution against a problem's cases, with the cap and the
    runner that decided it."""
    return Verification(
        id=new_id(),
        created_at=datetime.now(UTC),
        solution_id=solution_id,
        cap_ms=cap_ms,
        runner=runner,
        results=list(results),
    )


def site_outcome(
    site: CallSite,
    writing_id: str,
    *,
    provenance: MachineProvenance,
    target_template_id: str | None = None,
    target_technique: str | None = None,
    problem_id: str | None = None,
    gate: Gate | None = None,
    detail: str = "",
    mutants: int = 0,
    survived: int = 0,
    won: int = 0,
    killed: int = 0,
    rounds: list[int] | None = None,
    proposed: int = 0,
    misdeclared: int = 0,
    separating: int | None = None,
    repeats: int = 1,
    unseparated: str | None = None,
    largest: int | None = None,
) -> SiteOutcome:
    """`problem_id` is filled by the caller that lands the problem: a rejected
    draft mints none, and `writing_id` is what groups the four sites either
    way."""
    return SiteOutcome(
        id=new_id(),
        created_at=datetime.now(UTC),
        site=site,
        writing_id=writing_id,
        target_template_id=target_template_id,
        target_technique=target_technique,
        problem_id=problem_id,
        gate=gate,
        detail=detail,
        mutants=mutants,
        survived=survived,
        won=won,
        killed=killed,
        rounds=list(rounds or []),
        proposed=proposed,
        misdeclared=misdeclared,
        separating=separating,
        repeats=repeats,
        unseparated=unseparated,
        largest=largest,
        **provenance.model_dump(),
    )


def draft(
    writing_id: str,
    *,
    title: str,
    statement: str,
    canonical: str,
    declared: Sequence[DraftCase],
    difficulty: ProblemDifficulty,
    target_template_id: str | None = None,
    target_technique: str | None = None,
    provenance: MachineProvenance,
) -> Draft:
    """One writing, as the generator's call left it.

    The writing id rather than an id of its own: the four site outcomes of this
    writing already group under it, and a second identity would need a
    reference nothing else carries. The only minter here that is passed its id.
    """
    return Draft(
        id=writing_id,
        state=WritingState.DRAFTED,
        target_template_id=target_template_id,
        target_technique=target_technique,
        title=title,
        statement=statement,
        canonical=canonical,
        declared=list(declared),
        difficulty=difficulty,
        generator_provenance=provenance,
    )
