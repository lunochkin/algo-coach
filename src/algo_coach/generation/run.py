"""Writing several problems for one template, one after another.

Sequential on purpose, where the matcher runs its questions in parallel. Each
call is shown the statements the form already has, so two calls in flight
would be shown the same list and could write the same problem twice. What
concurrency would buy is minutes; what it costs is the diversity the brief
exists to enforce.

Nothing is stored here but the calls. A problem lands only once a canonical
has passed its cases and a reference has agreed with it, and the runner that
decides both comes after this.
"""

from collections.abc import Callable, Iterable

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.blind import reference
from algo_coach.generation.generator import (
    DEFAULT,
    Configuration,
    Draft,
    generate,
    written_for,
)
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Card, CaseOutcome, Problem, Template


class Failed(BaseModel):
    """One problem that was asked for and did not arrive."""

    index: int
    reason: str


class Drafted(BaseModel):
    """One problem as the two calls left it: written, and not yet verified.

    Called drafted rather than generated because nothing has run. The cases
    are the generator's own, the reference has not met them, and either could
    still discard the problem.
    """

    draft: Draft
    solution: str  # the reference, written from the statement alone
    call_id: str  # what wrote the problem
    reference_call_id: str


class Progress(BaseModel):
    """One problem, attempted. Reported as the run goes, since two calls per
    problem make a run of ten minutes long.

    The verdict and whether it landed are separate fields. A problem can be
    written and still not land — its canonical failing, or the two solutions
    disagreeing — and a report folding the two would say a call succeeded when
    nothing was kept.
    """

    index: int  # 1-based, over what this run asks for
    total: int
    template_slug: str
    title: str = ""
    cases: int = 0
    # how the canonical's run over those cases went, folded to its most severe
    # case. Absent where nothing ran, which is every problem until the runner
    # lands
    outcome: CaseOutcome | None = None
    landed: bool = False  # whether the problem, its cases and its solutions were stored
    reason: str | None = None  # the failure, when there was one


class GenerationResult(BaseModel):
    drafted: list[Drafted] = Field(default_factory=list)
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False


def write_one(
    transport: Transport,
    calls: CallLog,
    card: Card,
    template: Template,
    written: list[str],
    *,
    configuration: Configuration = DEFAULT,
) -> Drafted:
    """One problem: the statement, canonical and cases, then a reference
    written from the statement alone.

    The two calls in that order and never the reverse. The reference is what
    the statement is tested by, so it cannot exist before there is a statement
    to test.
    """
    draft, call = generate(
        transport, calls, card, template, written=written, configuration=configuration
    )
    solution, blind = reference(transport, calls, draft.statement, configuration=configuration)
    return Drafted(draft=draft, solution=solution, call_id=call.id, reference_call_id=blind.id)


def write_problems(
    transport: Transport,
    calls: CallLog,
    card: Card,
    template: Template,
    problems: Iterable[Problem],
    *,
    count: int = 1,
    configuration: Configuration = DEFAULT,
    on_progress: Callable[[Progress], None] | None = None,
) -> GenerationResult:
    """`count` problems for one template, each shown what came before it.

    A statement written by this run is added to the list the next call sees,
    without waiting for the problem to land. Nothing lands yet, and a run of
    ten would otherwise write ten problems against one list.

    A failure is one problem's, and the run continues — except that several in
    a row mean the configuration is broken rather than the model unlucky, which
    is what `ABORT_AFTER` catches.
    """
    result = GenerationResult()
    written = written_for(problems, template)
    consecutive = 0

    for index in range(1, count + 1):
        try:
            drafted = write_one(
                transport, calls, card, template, written, configuration=configuration
            )
        except Exception as failure:
            # Broad on purpose: a refusal, a rate limit or a reply that does
            # not parse costs this problem and not the run.
            result.failed.append(Failed(index=index, reason=repr(failure)))
            report(on_progress, index, count, template, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                result.aborted = True
                break
            continue

        consecutive = 0
        written.append(drafted.draft.statement)
        result.drafted.append(drafted)
        report(
            on_progress,
            index,
            count,
            template,
            title=drafted.draft.title,
            cases=len(drafted.draft.cases),
        )
    return result


def report(
    on_progress: Callable[[Progress], None] | None,
    index: int,
    total: int,
    template: Template,
    **outcome: object,
) -> None:
    if on_progress is not None:
        on_progress(Progress(index=index, total=total, template_slug=template.slug, **outcome))
