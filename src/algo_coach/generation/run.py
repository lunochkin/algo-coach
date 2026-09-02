"""Writing several problems for one template, one after another.

Sequential where the matcher is parallel: each call is shown the statements the
form already has, and two in flight would be shown the same list.
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
    """One problem that was written and did not survive its runs. Apart from
    `Failed`, which is a call that returned nothing."""

    index: int
    discard: str  # which gate rejected it
    reason: str


class Progress(BaseModel):
    """One problem, attempted. Reported as the run goes, since two calls per
    problem make a run of ten minutes long."""

    index: int  # 1-based, over what this run asks for
    total: int
    template_slug: str
    title: str = ""
    cases: int = 0
    # the canonical's run over those cases, folded to its severest. Absent
    # where the problem never reached a run
    outcome: CaseOutcome | None = None
    # apart from `outcome`: a problem can be written, run and still not land
    landed: bool = False
    reason: str | None = None


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
    # the `Checked` is returned rather than raised: a discard is a fact about
    # the problem, and the run reports what it cost
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

    A statement joins the list the next call sees without waiting for the
    problem to land, discarded ones included. `ABORT_AFTER` counts failures
    only: a discard means the calls answered and the runs rejected the writing.
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
            # broad on purpose: a refusal, a rate limit or a reply that does
            # not parse costs this problem and not the run
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
    # a count rather than the cases: the failing arguments are on the `Checked`
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
