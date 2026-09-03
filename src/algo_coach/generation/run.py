"""Writing several problems for one template, one after another.

Sequential where the matcher is parallel: each call is shown the statements the
form already has, and two in flight would be shown the same list.
"""

from collections.abc import Callable
from time import monotonic
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import reference
from algo_coach.generation.checks import CAP_MS, Checked, Discard, check
from algo_coach.generation.generator import (
    Configuration,
    GenerationError,
    generate,
    written_for,
)
from algo_coach.generation.hardening import harden
from algo_coach.generation.inputs import builder
from algo_coach.generation.landing import Corpus, Drafted, land
from algo_coach.generation.speedup import DRILL_CAP_MS, Missing, Searched, search
from algo_coach.generation.steps import SILENT, Notes, Step
from algo_coach.generation.writing import UNRECORDED, Writing
from algo_coach.outcomes import OutcomeLog
from algo_coach.runner import NoValue, outputs
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Call, CallSite, Card, CaseOutcome, SiteOutcome, Template


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
    # what the mutation loop did to the set: the mutants it enumerated, the
    # ones no case caught, and the cases the rounds appended
    mutants: int = 0
    survived: int = 0
    won: int = 0
    unmeasured: str | None = None  # the round's call failed, and the set is unmeasured


class Timing(BaseModel):
    """What the speedup search left. Both absent where the form is its own
    optimum and nothing was searched for."""

    separating: int | None = None  # the size the naive solution stops fitting at
    unseparated: str | None = None  # why there was none, where one was looked for


class Bar(BaseModel):
    """What the mutation loop reported. `unmeasured` is a call that failed,
    which costs the round rather than the problem."""

    mutants: int = 0
    survived: int = 0
    won: int = 0  # cases the rounds appended to the set
    unmeasured: str | None = None


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
    bench: Bench = BENCH,
    cap_ms: int = CAP_MS,
    notes: Notes = SILENT,
    writing: Writing = UNRECORDED,
) -> tuple[Drafted, Checked, Timing, Bar]:
    # the `Checked` is returned rather than raised: a discard is a fact about
    # the problem, and the run reports what it cost
    notes("statement", "writing the statement, the canonical and the cases")
    draft, call = generate(
        transport, calls, card, template, written=written, configuration=bench.generator
    )
    notes("statement", f"{draft.title!r}, {len(draft.cases)} case(s)", call)

    notes("reference", "writing the reference from the statement alone")
    solution, blind = reference(transport, calls, draft.statement, configuration=bench.blind)
    notes("reference", "written", blind)

    notes("cases", "running both solutions")
    started = monotonic()
    checked = check(
        draft.cases, canonical=draft.canonical, reference=solution, call=call, cap_ms=cap_ms
    )
    notes("cases", f"{settled(checked)}, {monotonic() - started:.1f}s in the runner")
    # both sites are recorded here rather than as they answer: what a gate
    # said about an answer is what the record carries, and the runs decide it
    writing(CallSite.GENERATOR, call, **gated(checked, Discard.NO_VALUE, Discard.MISDECLARED))
    writing(CallSite.BLIND, blind, **gated(checked, Discard.UNTESTED, Discard.DISAGREED))
    drafted = Drafted(
        draft=draft,
        solution=solution,
        call=call,
        reference_call=blind,
        cases=checked.cases,
    )
    if not checked.survived:
        return drafted, checked, Timing(), Bar()
    # the mutation loop before the timing case: what it wins is judged by the
    # cap a sitting judges under, and the separating input is chosen last
    checked, bar = measured(
        transport,
        calls,
        drafted,
        checked,
        configuration=bench.discrimination,
        cap_ms=cap_ms,
        notes=notes,
        writing=writing,
    )
    if not checked.survived:
        return drafted, checked, Timing(), bar
    checked, timing = timed(
        transport,
        calls,
        template,
        drafted,
        checked,
        configuration=bench.inputs,
        cap_ms=cap_ms,
        notes=notes,
        writing=writing,
    )
    return drafted, checked, timing, bar


def gated(checked: Checked, *gates: Discard) -> dict[str, object]:
    """The gate this site's answer was rejected by, and what it said. A discard
    belongs to the site whose output made it decidable."""
    if checked.discard not in gates:
        return {}
    return {"gate": checked.discard, "detail": why(checked)}


def settled(checked: Checked) -> str:
    """What the two runs left, as the stage line reports it."""
    if not checked.survived:
        return why(checked)
    return f"{checked.outcome}, {len(checked.cases)} case(s) settled"


def measured(
    transport: Transport,
    calls: CallLog,
    drafted: Drafted,
    checked: Checked,
    *,
    configuration: Configuration,
    cap_ms: int,
    notes: Notes = SILENT,
    writing: Writing = UNRECORDED,
) -> tuple[Checked, Bar]:
    """The mutation loop's cases, appended to the set the problem carries.

    A round's call that fails costs the round rather than the problem, as the
    speedup search's does.
    """
    try:
        hardened = harden(
            transport,
            calls,
            drafted.draft.statement,
            canonical=drafted.draft.canonical,
            reference=drafted.solution,
            cases=drafted.cases,
            slowest_ms=checked.slowest_ms,
            cap_ms=cap_ms,
            configuration=configuration,
            notes=notes,
        )
    except Exception as failure:
        notes("mutants", f"unmeasured: {failure!r}")
        return checked, Bar(unmeasured=repr(failure))

    bar = Bar(mutants=hardened.mutants, survived=hardened.survived, won=len(hardened.cases))
    # the loop's counters as the last round left them, which is why the record
    # cites that round's call. A loop needing none paid for no configuration
    writing(
        CallSite.DISCRIMINATION,
        hardened.call,
        gate=None if hardened.disagreement is None else Discard.DISAGREED,
        mutants=bar.mutants,
        survived=bar.survived,
        won=bar.won,
    )
    if hardened.disagreement is not None:
        # a boundary input the first case set never reached, answered two ways.
        # A canonical wrong there is what the loop exists to find
        discarded = Checked(
            outcome=checked.outcome,
            discard=Discard.DISAGREED,
            disagreements=[hardened.disagreement],
        )
        return discarded, bar
    drafted.cases.extend(hardened.cases)
    return checked, bar


def timed(
    transport: Transport,
    calls: CallLog,
    template: Template,
    drafted: Drafted,
    checked: Checked,
    *,
    configuration: Configuration,
    cap_ms: int,
    notes: Notes = SILENT,
    writing: Writing = UNRECORDED,
) -> tuple[Checked, Timing]:
    """The timing case, appended to the set where one was found.

    A search that fails costs the case rather than the problem, so its failure
    is caught here instead of reaching the run's abort count.
    """
    if not template.speedup:
        return checked, Timing()
    notes("timing", "searching for the input that separates the two solutions")
    try:
        found, built = separating(
            transport, calls, drafted, configuration=configuration, cap_ms=cap_ms, notes=notes
        )
    except Exception as failure:
        notes("timing", f"unsearched: {failure!r}")
        return checked, Timing(unseparated=repr(failure))

    writing(
        CallSite.INPUTS,
        built,
        gate=Discard.DISAGREED if found.missing is Missing.DISAGREED else None,
        separating=found.size,
        unseparated=found.missing,
    )
    if found.found:
        drafted.cases.append(found.case)
        notes("timing", f"separates at {found.size}")
        return checked, Timing(separating=found.size)
    notes("timing", f"no separation: {found.missing}")
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
    notes: Notes = SILENT,
) -> tuple[Searched, Call]:
    """One call for the input generator, then the search over the sizes it
    builds. The generation cap measures, and the sitting's cap is separated.

    The call is returned beside what the search found: the site's outcome is
    what the search decided about the code this call wrote.
    """
    built, call = builder(transport, calls, drafted.draft.statement, configuration=configuration)
    notes("timing", f"input generator written, up to {built.largest}", call)
    found = search(
        make(built.code, cap_ms),
        canonical=drafted.draft.canonical,
        reference=drafted.solution,
        call=call,
        cap_ms=DRILL_CAP_MS,
        largest=built.largest,
        measure_ms=cap_ms,
    )
    return found, call


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
    bench: Bench = BENCH,
    cap_ms: int = CAP_MS,
    on_progress: Callable[[Progress], None] | None = None,
    on_step: Callable[[Step], None] | None = None,
    outcomes: OutcomeLog | None = None,
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
        # filled as the sites answer and stored once the problem's fate is
        # known, which is the first point there is a problem id to name
        left: list[SiteOutcome] = []
        writing = Writing(template_id=template.id, into=left)
        try:
            drafted, checked, timing, bar = write_one(
                transport,
                calls,
                card,
                template,
                written,
                bench=bench,
                cap_ms=cap_ms,
                notes=Notes(on_step, index=index, total=count),
                writing=writing,
            )
        except Exception as failure:
            # broad on purpose: a refusal, a rate limit or a reply that does
            # not parse costs this problem and not the run
            result.failed.append(Failed(index=index, reason=repr(failure)))
            record(outcomes, left)
            report(on_progress, index, count, template, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                result.aborted = True
                break
            continue

        consecutive = 0
        written.append(drafted.draft.statement)
        if checked.survived:
            problem = land(corpus, template, drafted)
            record(outcomes, left, problem_id=problem.id)
            result.drafted.append(drafted)
        else:
            record(outcomes, left)
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
            mutants=bar.mutants,
            survived=bar.survived,
            won=bar.won,
            unmeasured=bar.unmeasured,
        )
    return result


def record(
    outcomes: OutcomeLog | None, left: list[SiteOutcome], *, problem_id: str | None = None
) -> None:
    """Appended after landing, since only then is there a problem to name. The
    `writing_id` groups them either way, which is what a discarded draft has."""
    if outcomes is None:
        return
    for outcome in left:
        outcomes.append(outcome.model_copy(update={"problem_id": problem_id}))


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
