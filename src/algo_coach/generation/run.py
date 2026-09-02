"""Writing several problems for one template, one after another.

Sequential where the matcher is parallel: each call is shown the statements the
form already has, and two in flight would be shown the same list.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.blind import reference
from algo_coach.generation.checks import CAP_MS, Checked, Discard, check
from algo_coach.generation.generator import (
    DEFAULT,
    Configuration,
    GenerationError,
    generate,
    written_for,
)
from algo_coach.generation.inputs import builder
from algo_coach.generation.landing import Corpus, Drafted, land
from algo_coach.generation.speedup import DRILL_CAP_MS, Missing, Searched, search
from algo_coach.runner import NoValue, outputs
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
    # the size at which the naive solution stops fitting a sitting. Absent
    # where the form is its own optimum, and `unseparated` says so where it is
    # not
    separating: int | None = None
    unseparated: str | None = None


class Timing(BaseModel):
    """What the speedup search left. Both absent where the form is its own
    optimum and nothing was searched for."""

    separating: int | None = None  # the size the naive solution stops fitting at
    unseparated: str | None = None  # why there was none, where one was looked for


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
) -> tuple[Drafted, Checked, Timing]:
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
    if not checked.survived:
        return drafted, checked, Timing()
    checked, timing = timed(
        transport, calls, template, drafted, checked, configuration=configuration, cap_ms=cap_ms
    )
    return drafted, checked, timing


def timed(
    transport: Transport,
    calls: CallLog,
    template: Template,
    drafted: Drafted,
    checked: Checked,
    *,
    configuration: Configuration,
    cap_ms: int,
) -> tuple[Checked, Timing]:
    """The timing case, appended to the set where one was found.

    A search that fails costs the case rather than the problem, so its failure
    is caught here instead of reaching the run's abort count.
    """
    if not template.speedup:
        return checked, Timing()
    try:
        found = separating(transport, calls, drafted, configuration=configuration, cap_ms=cap_ms)
    except Exception as failure:
        return checked, Timing(unseparated=repr(failure))

    if found.found:
        drafted.cases.append(found.case)
        return checked, Timing(separating=found.size)
    if found.missing is Missing.DISAGREED:
        # one input the small cases could not reach, answered two ways. A
        # canonical correct small and wrong large is discarded here
        discarded = Checked(
            outcome=checked.outcome,
            discard=Discard.DISAGREED,
            disagreements=[found.disagreement],
        )
        return discarded, Timing(unseparated=found.missing)
    return checked, Timing(unseparated=found.missing)


def separating(
    transport: Transport,
    calls: CallLog,
    drafted: Drafted,
    *,
    configuration: Configuration,
    cap_ms: int,
) -> Searched:
    """One call for the input generator, then the search over the sizes it
    builds. The generation cap measures, and the sitting's cap is separated."""
    built, _ = builder(transport, calls, drafted.draft.statement, configuration=configuration)
    return search(
        make(built.code, cap_ms),
        canonical=drafted.draft.canonical,
        reference=drafted.solution,
        cap_ms=DRILL_CAP_MS,
        largest=built.largest,
        measure_ms=cap_ms,
    )


def make(code: str, cap_ms: int) -> Callable[[int], list[Any]]:
    """The generator behind the callable the search takes: run through the
    executor as any other code, so nothing model-written runs in this process."""

    def built(size: int) -> list[Any]:
        [args] = outputs(code, [[size]], cap_ms=cap_ms)
        if isinstance(args, NoValue) or not isinstance(args, list):
            raise GenerationError(f"the input generator built nothing at size {size}")
        return args

    return built


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
            drafted, checked, timing = write_one(
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
            separating=timing.separating,
            unseparated=timing.unseparated,
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
