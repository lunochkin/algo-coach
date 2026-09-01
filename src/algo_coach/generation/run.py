"""Writing several problems for one template, one after another.

Sequential on purpose, where the matcher runs its questions in parallel. Each
call is shown the statements the form already has, so two calls in flight
would be shown the same list and could write the same problem twice. What
concurrency would buy is minutes; what it costs is the diversity the brief
exists to enforce.

Both solutions are run before a problem is kept, and one that fails a gate is
discarded whole — so a run reports what it wrote apart from what survived. A
surviving problem lands as it is written rather than at the end of the run: an
abort or a killed process then costs the problem in flight and nothing else.
"""

from collections.abc import Callable

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.blind import reference
from algo_coach.generation.checks import CAP_MS, Checked, Discard, check
from algo_coach.generation.generator import (
    DEFAULT,
    Configuration,
    generate,
    written_for,
)
from algo_coach.generation.landing import Corpus, Drafted, land
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Card, CaseOutcome, Template


class Failed(BaseModel):
    """One problem that was asked for and did not arrive."""

    index: int
    reason: str


class Discarded(BaseModel):
    """One problem that was written and did not survive its runs.

    Apart from `Failed`, which is a call that returned nothing. Both cost the
    same request and neither is kept, and a report folding them would say a
    model refused where it wrote a problem the runs rejected.
    """

    index: int
    discard: str  # which gate rejected it
    reason: str


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
    # case. Absent where the problem never reached a run, which is a call that
    # returned nothing
    outcome: CaseOutcome | None = None
    landed: bool = False  # whether the problem, its cases and its solutions were stored
    reason: str | None = None  # the failure, when there was one


class GenerationResult(BaseModel):
    drafted: list[Drafted] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
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
    cap_ms: int = CAP_MS,
) -> tuple[Drafted, Checked]:
    """One problem: the statement, canonical and cases, then a reference
    written from the statement alone.

    The two calls in that order and never the reverse. The reference is what
    the statement is tested by, so it cannot exist before there is a statement
    to test.

    Then both solutions run, and the `Checked` beside the problem says whether
    it survived. It is returned rather than raised: a discard is a fact about
    the problem, and the run reports what it cost.
    """
    draft, call = generate(
        transport, calls, card, template, written=written, configuration=configuration
    )
    solution, blind = reference(transport, calls, draft.statement, configuration=configuration)
    checked = check(draft.cases, canonical=draft.canonical, reference=solution, cap_ms=cap_ms)
    drafted = Drafted(
        draft=draft,
        solution=solution,
        call=call,
        reference_call=blind,
        cases=checked.cases,
    )
    return drafted, checked


def write_problems(
    transport: Transport,
    calls: CallLog,
    card: Card,
    template: Template,
    corpus: Corpus,
    *,
    count: int = 1,
    configuration: Configuration = DEFAULT,
    cap_ms: int = CAP_MS,
    on_progress: Callable[[Progress], None] | None = None,
) -> GenerationResult:
    """`count` problems for one template, each shown what came before it, and
    each stored as soon as its runs keep it.

    A statement written by this run is added to the list the next call sees,
    without waiting for the problem to land. A discarded one is added too, so a
    run of ten writes ten problems rather than ten variants of one.

    A failure is one problem's, and the run continues — except that several in
    a row mean the configuration is broken rather than the model unlucky, which
    is what `ABORT_AFTER` catches. A discard is not counted there: the calls
    answered, and what the runs rejected is the model's writing rather than the
    configuration.

    A discarded statement is still shown to the next call. It was written for
    this form, and asking for it again is what the list exists to prevent.
    """
    result = GenerationResult()
    written = written_for(corpus.problems.all(), template)
    consecutive = 0

    for index in range(1, count + 1):
        try:
            drafted, checked = write_one(
                transport,
                calls,
                card,
                template,
                written,
                configuration=configuration,
                cap_ms=cap_ms,
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
        if checked.survived:
            land(corpus, template, drafted)
            result.drafted.append(drafted)
        else:
            result.discarded.append(
                Discarded(index=index, discard=checked.discard, reason=why(checked))
            )
        report(
            on_progress,
            index,
            count,
            template,
            title=drafted.draft.title,
            cases=len(drafted.draft.cases),
            outcome=checked.outcome,
            landed=checked.survived,
            reason=None if checked.survived else why(checked),
        )
    return result


def why(checked: Checked) -> str:
    """The discard as one line, naming what it was decided on.

    A count rather than the cases themselves: the gate is what a run reports,
    and the arguments that failed are on the `Checked` for a reader who wants
    them.
    """
    match checked.discard:
        case Discard.NO_VALUE:
            return f"discarded: the canonical {checked.outcome} on some case"
        case Discard.MISDECLARED:
            return f"discarded: the canonical contradicts {len(checked.misdeclarations)} case(s)"
        case Discard.UNTESTED:
            return "discarded: the reference computed no case"
        case _:
            return f"discarded: the two solutions disagree on {len(checked.disagreements)} case(s)"


def report(
    on_progress: Callable[[Progress], None] | None,
    index: int,
    total: int,
    template: Template,
    **outcome: object,
) -> None:
    if on_progress is not None:
        on_progress(Progress(index=index, total=total, template_slug=template.slug, **outcome))
