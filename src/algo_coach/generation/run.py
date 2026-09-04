"""Writing several problems for one template, one after another. Sequential
where the matcher is parallel — `flows.md` gives why."""

from collections.abc import Callable
from time import monotonic
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.drafts import DraftStore
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import reference
from algo_coach.generation.checks import CAP_MS, Checked, Discard, agree, check, stopped
from algo_coach.generation.fuzzing import Fuzzing, pass_over
from algo_coach.generation.generator import (
    Configuration,
    GenerationError,
    generate,
    written_for,
)
from algo_coach.generation.hardening import harden
from algo_coach.generation.inputs import Built, builder
from algo_coach.generation.landing import Corpus, land, written_by
from algo_coach.generation.speedup import DRILL_CAP_MS, Missing, search
from algo_coach.generation.steps import SILENT, Notes, Step
from algo_coach.generation.writing import UNRECORDED, Writing
from algo_coach.outcomes import OutcomeLog
from algo_coach.runner import NoValue, outputs
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import (
    Call,
    CallSite,
    Card,
    CaseOutcome,
    Draft,
    MachineProvenance,
    SettledCase,
    SiteOutcome,
    Template,
    WritingState,
)

# the seed the speedup search builds at, which never varies: the halving
# compares one size against another, so two inputs of one shape are needed
SEARCH_SEED = 0


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
    unbuilt: str | None = None  # the input generator's call failed, so nothing was built
    # what the mutation loop did to the set: the mutants it enumerated, the
    # ones no case caught, and the cases the rounds appended
    mutants: int = 0
    survived: int = 0
    won: int = 0
    offered: int = 0  # what the rounds proposed, so the difference killed nothing
    # the fuzz pass before the rounds: what it built and what it kept
    built: int = 0
    kept: int = 0
    # which source killed what: the cases written with the statement, the fuzz
    # pass's built inputs, and one entry per round
    declared: int = 0
    fuzzed: int = 0
    caught: list[int] = Field(default_factory=list)
    unmeasured: str | None = None  # the round's call failed, and the set is unmeasured


class Inputs(BaseModel):
    """What the inputs site left: the code it wrote to build an input, and what
    the speedup search made of that code.

    The generator is written for every problem, so `built` stands where the
    search never ran. Both search fields are absent where the form is its own
    optimum and nothing was looked for.
    """

    call: Call | None = None
    built: Built | None = None
    unbuilt: str | None = None  # the call failed, and no code was written
    separating: int | None = None  # the size the naive solution stops fitting at
    unseparated: str | None = None  # why there was none, where one was looked for
    gate: Discard | None = None  # the two solutions disagreed at that size


class Bar(BaseModel):
    """What the mutation loop reported. `unmeasured` is a call that failed,
    which costs the round rather than the problem."""

    mutants: int = 0
    survived: int = 0
    won: int = 0  # cases the rounds appended to the set
    offered: int = 0  # what they proposed to it, so the difference killed nothing
    # the fuzz pass before them: the inputs it built and the ones it kept,
    # which cost subprocesses rather than a call
    built: int = 0
    kept: int = 0
    # which source killed what, each written on the site whose output did it
    declared: int = 0
    fuzzed: int = 0
    caught: list[int] = Field(default_factory=list)
    # the last round's call, which is what the counters were left by. Absent
    # where nothing reached a round
    call: Call | None = None
    # a round's proposal the two solutions answered differently. The fuzz
    # pass's own is the inputs site's, since its code built the input
    gate: Discard | None = None
    unmeasured: str | None = None


class Held(BaseModel):
    """One draft that passed every gate and stopped short of landing: where it
    stopped, and what the step that stopped it left.

    The reason is carried rather than read back from the site outcomes, since
    a run reports what it did before anything reads its log.
    """

    index: int
    draft: Draft
    # the size the search proved a separation at, and why it stored no case
    separating: int | None = None
    unseparated: str | None = None
    unbuilt: str | None = None  # no input generator, so no search ran at all
    unmeasured: str | None = None  # the round's call failed


class GenerationResult(BaseModel):
    drafted: list[Draft] = Field(default_factory=list)
    # written whole and demonstrating nothing, so held until a resume separates
    # it, the template's `speedup` is corrected, or it is rejected
    held: list[Held] = Field(default_factory=list)
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
    drafts: DraftStore | None = None,
) -> tuple[Draft, Checked, Inputs, Bar]:
    # the `Checked` is returned rather than raised: a discard is a fact about
    # the problem, and the run reports what it cost
    notes("statement", "writing the statement, the canonical and the cases")
    generated, call = generate(
        transport, calls, card, template, written=written, configuration=bench.generator
    )
    notes("statement", f"{generated.title!r}, {len(generated.cases)} case(s)", call)
    draft = held(drafts, writing.draft(generated, call))

    notes("cases", "running the canonical against what its own call declared")
    started = monotonic()
    ran = check(generated.cases, canonical=generated.canonical, cap_ms=cap_ms)
    if not ran.survived:
        rejected = stopped(ran)
        notes("cases", why(rejected))
        draft = held(drafts, moved(draft, WritingState.REJECTED, gate=ran.discard))
        sites(writing, call, None, rejected, Inputs(), Bar())
        return draft, rejected, Inputs(), Bar()
    draft = held(drafts, moved(draft, WritingState.CHECKED))

    notes("reference", "writing the reference from the statement alone")
    solution, blind = reference(transport, calls, generated.statement, configuration=bench.blind)
    notes("reference", "written", blind)
    draft = held(
        drafts,
        moved(draft, WritingState.REFERENCED, reference=solution, blind=copied_from(blind)),
    )

    checked = agree(ran, generated.cases, reference=solution, call=call, cap_ms=cap_ms)
    notes("cases", f"{settled(checked)}, {monotonic() - started:.1f}s in the runner")
    # kept because `checked` is replaced by a later gate: the first two sites
    # are judged by the runs of the first case set and by nothing after them
    first = checked
    if not checked.survived:
        draft = held(drafts, moved(draft, WritingState.REJECTED, gate=checked.discard))
        sites(writing, call, blind, first, Inputs(), Bar())
        return draft, checked, Inputs(), Bar()
    draft = held(drafts, moved(draft, WritingState.AGREED, cases=checked.cases))

    # written before the mutation loop, and for every problem: the inputs it
    # builds are what a fuzz pass kills mutants with, and a round is then paid
    # for the survivors alone
    inputs = building(
        transport, calls, generated.statement, configuration=bench.inputs, notes=notes
    )
    if inputs.built is not None:
        draft = held(
            drafts,
            moved(
                draft,
                WritingState.BUILT,
                builder=inputs.built.code,
                largest=inputs.built.largest,
                inputs=copied_from(inputs.call),
            ),
        )
    # before the loop, so a canonical wrong at scale costs no round. The case
    # is held back until after it: the survivors are decided against the set as
    # the statement left it
    checked, inputs, separating = timed(
        template, draft, checked, inputs, cap_ms=cap_ms, notes=notes
    )
    if not checked.survived:
        draft = held(drafts, moved(draft, WritingState.REJECTED, gate=checked.discard))
        sites(writing, call, blind, first, inputs, Bar())
        return draft, checked, inputs, Bar()
    if template.speedup and inputs.built is not None:
        draft = held(drafts, moved(draft, WritingState.SEARCHED, separating=separating))
    if template.speedup and separating is None:
        # the claim is what a rung teaches, and a landed problem is repaired
        # nowhere: the draft stops at the step that has no answer, and a resume
        # is what carries it forward
        sites(writing, call, blind, first, inputs, Bar())
        return draft, checked, inputs, Bar()

    checked, inputs, bar, won = measured(
        transport,
        calls,
        draft,
        checked,
        inputs,
        configuration=bench.discrimination,
        cap_ms=cap_ms,
        notes=notes,
    )
    if not checked.survived:
        draft = held(drafts, moved(draft, WritingState.REJECTED, gate=checked.discard))
        sites(writing, call, blind, first, inputs, bar)
        return draft, checked, inputs, bar
    if bar.unmeasured is not None:
        # the round's call failed, so the set is what the statement left. Held
        # at the step before the loop, since a resume asks again where landing
        # would store a set no round was paid for
        sites(writing, call, blind, first, inputs, bar)
        return draft, checked, inputs, bar
    draft = held(
        drafts,
        moved(draft, WritingState.HARDENED, won=won, discrimination=copied_from(bar.call)),
    )
    sites(writing, call, blind, first, inputs, bar)
    return draft, checked, inputs, bar


def held(drafts: DraftStore | None, draft: Draft) -> Draft:
    """Written after every step that moved it, so a run that dies leaves the
    draft where it stopped. Silent without a store, as `Writing` is."""
    if drafts is not None:
        drafts.put(draft)
    return draft


def cleared(drafts: DraftStore | None, draft: Draft) -> None:
    """The draft is working state, and the problem it became is what a reader
    finds. Nothing in it is re-derivable from anywhere else, so clearing it is
    what landing means."""
    if drafts is not None:
        drafts.remove(draft.id)


def swept(drafts: DraftStore | None) -> None:
    """A draft naming a problem landed and was not cleared, so the run that
    wrote it died between the two. Cleared here, since writing the problem
    again is the only other way to finish it."""
    if drafts is None:
        return
    for draft in drafts.all():
        if draft.state is WritingState.LANDED:
            drafts.remove(draft.id)


def moved(draft: Draft, state: WritingState, **fields: Any) -> Draft:
    """Revised in place rather than appended: the draft store is working state,
    and a step's answer moves the draft it was written on."""
    return Draft.model_validate(draft.model_dump() | {"state": state} | fields)


def reject(drafts: DraftStore | None, draft: Draft, gate: Discard = Discard.UNEXERCISED) -> Draft:
    """The exit a held draft takes where no resume would separate it: the
    reference wrote the form, so the claim holds and this problem does not
    exercise it. Read by hand, since the run cannot tell that answer from an
    input generator that built the wrong shape.

    A landed draft is not rejected. It names a problem a reader already finds,
    and clearing it is what landing means, so one still in the store is a
    crash's leftover rather than a writing to reject.
    """
    if draft.state in (WritingState.LANDED, WritingState.REJECTED):
        raise ValueError(f"a {draft.state} draft is not rejected")
    return held(drafts, moved(draft, WritingState.REJECTED, gate=gate))


def copied_from(call: Call | None) -> MachineProvenance | None:
    """The configuration of one step's call, as a site outcome copies it."""
    if call is None:
        return None
    return MachineProvenance.model_validate(written_by(call))


def sites(
    writing: Writing,
    call: Call,
    blind: Call | None,
    ran: Checked,
    inputs: Inputs,
    bar: Bar,
) -> None:
    """The four records of one attempt, written once the loop's numbers are
    known.

    A gate belongs to the site whose answer made it decidable, and a kill to
    the site whose output did it. Each is written where its own counter can be
    other than zero, so the three sources sum whatever the run stopped at: the
    generator always answered, the fuzz pass ran only where a generator was
    written, and a round killed only where one was asked.
    """
    writing(
        CallSite.GENERATOR,
        call,
        **gated(ran, Discard.NO_VALUE, Discard.MISDECLARED),
        mutants=bar.mutants,
        killed=bar.declared,
    )
    writing(CallSite.BLIND, blind, **gated(ran, Discard.UNTESTED, Discard.DISAGREED))
    # the counters as the last round left them, which is why the record cites
    # that round's call. A loop needing none paid for no configuration
    writing(
        CallSite.DISCRIMINATION,
        bar.call,
        gate=bar.gate,
        survived=bar.survived,
        won=bar.won,
        offered=bar.offered,
        killed=sum(bar.caught),
        rounds=bar.caught,
    )
    writing(
        CallSite.INPUTS,
        inputs.call,
        gate=inputs.gate,
        killed=bar.fuzzed,
        separating=inputs.separating,
        unseparated=inputs.unseparated,
    )


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
    draft: Draft,
    checked: Checked,
    inputs: Inputs,
    *,
    configuration: Configuration,
    cap_ms: int,
    notes: Notes = SILENT,
) -> tuple[Checked, Inputs, Bar, list[SettledCase]]:
    """The mutation loop's cases, appended to the set the problem carries.

    `inputs` is returned because the fuzz pass runs inside the loop: a built
    input the two solutions answer differently is the inputs site's gate, since
    nothing was decidable before its code built one.

    A round's call that fails costs the round rather than the problem, as the
    speedup search's does.
    """
    try:
        hardened = harden(
            transport,
            calls,
            draft.statement,
            canonical=draft.canonical,
            reference=draft.reference or "",
            cases=draft.cases,
            slowest_ms=checked.slowest_ms,
            cap_ms=cap_ms,
            configuration=configuration,
            fuzzing=fuzzing(draft, inputs, cap_ms=cap_ms),
            notes=notes,
        )
    except Exception as failure:
        notes("mutants", f"unmeasured: {failure!r}")
        return checked, inputs, Bar(unmeasured=repr(failure)), []

    kept = len(hardened.fuzzed.cases) if hardened.fuzzed else 0
    bar = Bar(
        mutants=hardened.mutants,
        survived=hardened.survived,
        # the rounds' own, which is what the site is scored on. The pass before
        # them paid for no call
        won=len(hardened.cases) - kept,
        offered=hardened.offered,
        built=hardened.fuzzed.built if hardened.fuzzed else 0,
        kept=kept,
        declared=hardened.declared,
        fuzzed=hardened.fuzzed.killed if hardened.fuzzed else 0,
        caught=hardened.caught,
        call=hardened.call,
    )
    if hardened.disagreement is None:
        return checked, inputs, bar, hardened.cases

    # a boundary input the first case set never reached, answered two ways
    discarded = Checked(
        outcome=checked.outcome,
        discard=Discard.DISAGREED,
        disagreements=[hardened.disagreement],
    )
    # the fuzz pass's input was built by the inputs site's code, so its gate is
    # filed there and the round answered for nothing
    if hardened.fuzzed is not None and hardened.fuzzed.disagreement is not None:
        return discarded, inputs.model_copy(update={"gate": Discard.DISAGREED}), bar, []
    return discarded, inputs, bar.model_copy(update={"gate": Discard.DISAGREED}), []


def building(
    transport: Transport,
    calls: CallLog,
    statement: str,
    *,
    configuration: Configuration,
    notes: Notes = SILENT,
) -> Inputs:
    """The code that builds an input of a given size, for every problem.

    A call that fails costs the inputs rather than the problem: it says nothing
    about the statement, as a failed search does not.
    """
    notes("inputs", "writing the input generator")
    try:
        built, call = builder(transport, calls, statement, configuration=configuration)
    except Exception as failure:
        notes("inputs", f"unbuilt: {failure!r}")
        return Inputs(unbuilt=repr(failure))
    notes("inputs", f"written, up to {built.largest}", call)
    return Inputs(call=call, built=built)


def fuzzing(draft: Draft, inputs: Inputs, *, cap_ms: int) -> Fuzzing | None:
    """The pass `harden` runs before its first round, or nothing where no
    generator was written for it to build with."""
    if inputs.built is None or inputs.call is None:
        return None
    return pass_over(
        inputs.built,
        canonical=draft.canonical,
        reference=draft.reference or "",
        call=inputs.call,
        cap_ms=cap_ms,
    )


def timed(
    template: Template,
    draft: Draft,
    checked: Checked,
    inputs: Inputs,
    *,
    cap_ms: int,
    notes: Notes = SILENT,
) -> tuple[Checked, Inputs, SettledCase | None]:
    """The timing case, returned rather than appended: the caller holds it back
    until the mutation loop has run. The generation cap measures, and the
    sitting's cap is what a size is separated against.

    A search that fails costs the case rather than the problem, so its failure
    is caught here instead of reaching the run's abort count.
    """
    if not template.speedup or inputs.built is None:
        return checked, inputs, None
    notes("timing", "searching for the input that separates the two solutions")
    try:
        found = search(
            make(inputs.built.code, cap_ms),
            canonical=draft.canonical,
            reference=draft.reference or "",
            call=inputs.call,
            cap_ms=DRILL_CAP_MS,
            largest=inputs.built.largest,
            measure_ms=cap_ms,
        )
    except Exception as failure:
        notes("timing", f"unsearched: {failure!r}")
        return checked, inputs.model_copy(update={"unseparated": repr(failure)}), None

    if found.found:
        notes("timing", f"separates at {found.size}")
        return checked, inputs.model_copy(update={"separating": found.size}), found.case
    notes("timing", f"no case: {found.missing}")
    searched = inputs.model_copy(
        update={
            # carried where the search proved a separation and stored nothing,
            # which `unseparated` beside it is what tells apart from a stored one
            "separating": found.size,
            "unseparated": found.missing,
            "gate": Discard.DISAGREED if found.missing is Missing.DISAGREED else None,
        }
    )
    if found.missing is not Missing.DISAGREED:
        return checked, searched, None
    # one input the small cases could not reach, answered two ways
    discarded = Checked(
        outcome=checked.outcome,
        discard=Discard.DISAGREED,
        disagreements=[found.disagreement],
    )
    return discarded, searched, None


def make(code: str, cap_ms: int, *, seed: int = SEARCH_SEED) -> Callable[[int], list[Any]]:
    """The generator behind the callable the search takes: run through the
    executor as any other code, so nothing model-written runs in this process.

    One seed throughout, or the halving would compare two different inputs.
    """

    def built(size: int) -> list[Any]:
        [args] = outputs(code, [[size, seed]], cap_ms=cap_ms)
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
    drafts: DraftStore | None = None,
) -> GenerationResult:
    """`count` problems for one template, each shown what came before it, and
    each stored as soon as its runs keep it.

    A statement joins the list the next call sees without waiting for the
    problem to land, discarded ones included. `ABORT_AFTER` counts failures
    only: a discard means the calls answered and the runs rejected the writing.
    """
    result = GenerationResult()
    swept(drafts)
    written = written_for(corpus.problems.all(), template)
    consecutive = 0

    for index in range(1, count + 1):
        # filled as the sites answer and stored once the problem's fate is
        # known, which is the first point there is a problem id to name
        left: list[SiteOutcome] = []
        writing = Writing(template_id=template.id, into=left)
        try:
            draft, checked, inputs, bar = write_one(
                transport,
                calls,
                card,
                template,
                written,
                bench=bench,
                cap_ms=cap_ms,
                notes=Notes(on_step, index=index, total=count),
                writing=writing,
                drafts=drafts,
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
        written.append(draft.statement)
        if checked.survived and draft.state is not WritingState.HARDENED:
            # every gate that judges the problem passed, and a step of the
            # writing did not: held where it stopped rather than landed
            record(outcomes, left)
            result.held.append(
                Held(
                    index=index,
                    draft=draft,
                    separating=inputs.separating,
                    unseparated=inputs.unseparated,
                    unbuilt=inputs.unbuilt,
                    unmeasured=bar.unmeasured,
                )
            )
        elif checked.survived:
            problem = land(corpus, template, draft)
            # named before it is cleared: a crash between the two then leaves a
            # draft the next run clears rather than a problem written twice
            draft = held(drafts, moved(draft, WritingState.LANDED, problem_id=problem.id))
            cleared(drafts, draft)
            record(outcomes, left, problem_id=problem.id)
            result.drafted.append(draft)
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
            title=draft.title,
            cases=len(draft.declared),
            outcome=checked.outcome,
            landed=draft.state is WritingState.LANDED,
            reason=None if checked.survived else why(checked),
            separating=inputs.separating,
            unseparated=inputs.unseparated,
            unbuilt=inputs.unbuilt,
            mutants=bar.mutants,
            survived=bar.survived,
            won=bar.won,
            offered=bar.offered,
            built=bar.built,
            kept=bar.kept,
            declared=bar.declared,
            fuzzed=bar.fuzzed,
            caught=bar.caught,
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
