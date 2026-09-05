"""One draft carried through the steps after the statement, in the order
`flows.md` gives. Each step is asked again only where its own configuration or
digest moved."""

from dataclasses import dataclass, field
from time import monotonic

from algo_coach.calls import CallLog, Transport
from algo_coach.drafts import DraftStore
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import reference
from algo_coach.generation.checks import (
    CAP_MS,
    Checked,
    Discard,
    agree,
    check,
    stopped,
    wrong_on,
)
from algo_coach.generation.clock import naive
from algo_coach.generation.drafting import advanced, held, rejected
from algo_coach.generation.fuzzing import Fuzzing, pass_over
from algo_coach.generation.generator import generate
from algo_coach.generation.hardening import harden
from algo_coach.generation.inputs import Built, builder
from algo_coach.generation.resuming import draws_again, re_asks, reaches
from algo_coach.generation.steps import SILENT, Notes
from algo_coach.generation.timing import timed
from algo_coach.generation.verdicts import (
    Bar,
    Clock,
    Inputs,
    barred,
    blind_verdicts,
    gated,
    loop_verdicts,
    search_verdicts,
    settled,
    why,
)
from algo_coach.generation.writing import UNRECORDED, Writing
from algo_coach.schema import (
    Call,
    CallSite,
    Card,
    Configuration,
    Draft,
    MachineProvenance,
    SettledCase,
    Template,
    WritingState,
)


@dataclass
class Passage:
    """One draft carried through the steps after the statement: what the steps
    are handed, and what each of them left.

    `first` is the first case set's verdict, which the first two sites are
    judged by. A later gate replaces `checked` and leaves it. `start` is where
    a resume began, and the search reads it: it runs the builder against the
    clock, so either site moving takes it again.
    """

    transport: Transport
    calls: CallLog
    template: Template
    draft: Draft
    start: WritingState
    bench: Bench = BENCH
    cap_ms: int = CAP_MS
    notes: Notes = SILENT
    drafts: DraftStore | None = None
    checked: Checked = field(default_factory=lambda: Checked(outcome=None))
    first: Checked = field(default_factory=lambda: Checked(outcome=None))
    blind: Call | None = None
    inputs: Inputs = field(default_factory=Inputs)
    clock: Clock = field(default_factory=Clock)
    bar: Bar = field(default_factory=Bar)

    @property
    def generator(self) -> MachineProvenance:
        """The configuration of the call that wrote the draft. `carried` has
        checked it is there before any step reads it."""
        if self.draft.generator is None:
            raise ValueError("a draft carries the configuration of the call that wrote it")
        return self.draft.generator

    @property
    def measurable(self) -> bool:
        """Whether a search has anything to run: a speedup is claimed and there
        is a builder to make inputs with."""
        return self.template.speedup and self.inputs.built is not None


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
) -> Passage:
    # the `Checked` is returned rather than raised: a discard is a fact about
    # the problem, and the run reports what it cost
    notes("statement", "writing the statement, the canonical and the cases")
    generated, call = generate(
        transport, calls, card, template, written=written, configuration=bench.generator
    )
    notes("statement", f"{generated.title!r}, {len(generated.cases)} case(s)", call)
    draft = held(drafts, writing.draft(generated, call))
    passage = Passage(
        transport,
        calls,
        template,
        draft,
        WritingState.CHECKED,
        bench=bench,
        cap_ms=cap_ms,
        notes=notes,
        drafts=drafts,
    )
    return carried(passage, writing, generator=call)


def carried(passage: Passage, writing: Writing, *, generator: Call | None) -> Passage:
    """Every step after the statement. Each site is asked again only where its
    own configuration or digest moved, so a resume pays for the calls that
    moved and for no others.

    The local runs are taken again either way: the draft stores what a call
    produced, and a subprocess answers the rest for nothing. The steps stop at
    the first that rejects or holds the draft, and the site records are written
    once, over whatever they left.
    """
    if passage.draft.generator is None:
        raise ValueError("a draft carries the configuration of the call that wrote it")
    for step in STEPS:
        if not step(passage):
            break
    sites(writing, generator, passage)
    return passage


def to_agreed(p: Passage) -> bool:
    """The canonical against its own declarations, then the blind reference
    against the canonical."""
    p.notes("cases", "running the canonical against what its own call declared")
    started = monotonic()
    ran = check(p.draft.declared, canonical=p.draft.canonical, cap_ms=p.cap_ms)
    if not ran.survived:
        p.checked = p.first = stopped(ran)
        p.notes("cases", why(p.first))
        p.draft = rejected(p.drafts, p.draft, ran.discard)
        return False
    p.draft = advanced(p.drafts, p.draft, WritingState.CHECKED)

    if re_asks(p.draft, "blind", p.template, p.bench) or p.draft.reference is None:
        p.notes("reference", "writing the reference from the statement alone")
        solution, p.blind = reference(
            p.transport, p.calls, p.draft.statement, configuration=p.bench.blind
        )
        p.notes("reference", "written", p.blind)
        p.draft = advanced(
            p.drafts,
            p.draft,
            WritingState.REFERENCED,
            reference=solution,
            blind=MachineProvenance.of(p.blind),
        )
    else:
        p.notes("reference", "reused, at the configuration that wrote it")
        solution = p.draft.reference

    # the generator's configuration rather than the blind call's: the arguments
    # are the statement's own cases, whoever computed what they return
    p.checked = p.first = agree(
        ran, p.draft.declared, reference=solution, written=p.generator, cap_ms=p.cap_ms
    )
    p.notes("cases", f"{settled(p.first)}, {monotonic() - started:.1f}s in the runner")
    if not p.first.survived:
        p.draft = rejected(p.drafts, p.draft, p.first.discard)
        return False
    p.draft = advanced(p.drafts, p.draft, WritingState.AGREED, cases=p.first.cases)
    return True


def to_built(p: Passage) -> bool:
    """The input generator, before the mutation loop and for every problem: the
    inputs it builds are what a fuzz pass kills mutants with, and a round is
    then paid for the survivors alone. A call that fails stops nothing here:
    the draft is held at the step that has no answer."""
    if re_asks(p.draft, "inputs", p.template, p.bench) or p.draft.builder is None:
        p.inputs = building(
            p.transport, p.calls, p.draft.statement, configuration=p.bench.inputs, notes=p.notes
        )
        if p.inputs.built is not None:
            p.draft = advanced(
                p.drafts,
                p.draft,
                WritingState.BUILT,
                builder=p.inputs.built.code,
                largest=p.inputs.built.largest,
                inputs=MachineProvenance.of(p.inputs.call),
            )
    else:
        p.notes("inputs", "reused, at the configuration that wrote it")
        p.inputs = stored(p.draft)
    return True


def to_paced(p: Passage) -> bool:
    """The clock, after the builder and only where a speedup is claimed: the
    builder is written for every problem, and nothing measures a form that is
    its own optimum. A draft with no builder stops at the step before this one,
    so paying for a clock here would buy a step the draft cannot record."""
    if not p.measurable:
        return True
    p.clock = paced(
        p.transport,
        p.calls,
        p.draft,
        p.template,
        configuration=p.bench.clock,
        cap_ms=p.cap_ms,
        notes=p.notes,
        # drawn again where the search separated nothing, though nothing about
        # the bench moved: the site is the one that is sampled
        reuse=not re_asks(p.draft, "clock", p.template, p.bench)
        and not draws_again(p.draft, p.template),
    )
    if p.clock.code is not None and p.clock.call is not None:
        p.draft = advanced(
            p.drafts,
            p.draft,
            WritingState.PACED,
            naive=p.clock.code,
            clock=MachineProvenance.of(p.clock.call),
        )
    # without a clock the search has nothing to measure the canonical against,
    # so the draft stops here rather than at the step after it
    return p.clock.code is not None


def to_searched(p: Passage) -> bool:
    """The separating case, before the loop so a canonical wrong at scale costs
    no round. It is held back until after the loop: the survivors are decided
    against the set as the statement left it."""
    separating = p.draft.separating
    if reaches(p.start, WritingState.SEARCHED):
        p.checked, p.inputs, separating = timed(
            p.template, p.draft, p.checked, p.inputs, p.clock, cap_ms=p.cap_ms, notes=p.notes
        )
        if not p.checked.survived:
            p.draft = rejected(p.drafts, p.draft, p.checked.discard)
            return False
        if p.measurable:
            p.draft = advanced(
                p.drafts,
                p.draft,
                WritingState.SEARCHED,
                separating=separating,
                unseparated=p.inputs.unseparated,
            )
    # the claim is what a rung teaches, and a landed problem is repaired
    # nowhere: the draft stops at the step that has no answer, and a resume is
    # what carries it forward
    return not (p.template.speedup and separating is None)


def to_hardened(p: Passage) -> bool:
    """The mutation loop over the set the two solutions settled."""
    p.checked, p.inputs, p.bar, won = measured(
        p.transport,
        p.calls,
        p.draft,
        p.checked,
        p.inputs,
        configuration=p.bench.discrimination,
        cap_ms=p.cap_ms,
        notes=p.notes,
    )
    if not p.checked.survived:
        p.draft = rejected(p.drafts, p.draft, p.checked.discard)
        return False
    if p.bar.unmeasured is not None:
        # the round's call failed, so the set is what the statement left. Held
        # at the step before the loop, since a resume asks again where landing
        # would store a set no round was paid for
        return False
    p.draft = advanced(
        p.drafts,
        p.draft,
        WritingState.HARDENED,
        won=won,
        discrimination=MachineProvenance.of(p.bar.call),
    )
    return True


# in the order `flows.md` gives, each named by the state it reaches
STEPS = (to_agreed, to_built, to_paced, to_searched, to_hardened)


def stored(draft: Draft) -> Inputs:
    """The input generator a draft already holds, at the configuration that
    wrote it. It made no call here, so it leaves no site outcome."""
    return Inputs(
        built=Built(code=draft.builder or "", largest=draft.largest or 1),
        written=draft.inputs,
    )


def sites(writing: Writing, call: Call | None, p: Passage) -> None:
    """The five records of one attempt, written once the loop's numbers are
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
        **gated(p.first, Discard.NO_VALUE),
        mutants=p.bar.mutants,
        killed=p.bar.declared,
        misdeclared=len(p.first.misdeclarations),
    )
    writing(CallSite.BLIND, p.blind, **blind_verdicts(p.first))
    # the counters as the last round left them, which is why the record cites
    # that round's call. A loop needing none paid for no configuration
    writing(CallSite.DISCRIMINATION, p.bar.call, **loop_verdicts(p.bar))
    writing(CallSite.INPUTS, p.inputs.call, **search_verdicts(p.inputs), killed=p.bar.fuzzed)
    # the search judged this answer as much as the builder's, so both records
    # carry its verdict. A resume that re-asked one writes only that one
    writing(
        CallSite.CLOCK,
        p.clock.call,
        separating=p.inputs.separating,
        unseparated=p.inputs.unseparated,
    )


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

    bar = barred(hardened)
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
    return Inputs(call=call, built=built, written=MachineProvenance.of(call))


def paced(
    transport: Transport,
    calls: CallLog,
    draft: Draft,
    template: Template,
    *,
    configuration: Configuration,
    cap_ms: int,
    notes: Notes = SILENT,
    reuse: bool = True,
) -> Clock:
    """The naive solution, or the one the draft already holds, run against the
    set the two solutions settled.

    A call that fails costs the clock rather than the problem, as a failed
    builder does. So does one whose answer is wrong: what it says is that this
    solution measures nothing, not that the statement is unsound.
    """
    if reuse and draft.naive is not None:
        notes("clock", "reused, at the configuration that wrote it")
        clock = Clock(code=draft.naive, written=draft.clock)
    else:
        notes("clock", "writing the solution the search measures against")
        try:
            code, call = naive(
                transport, calls, draft.statement, template.trigger, configuration=configuration
            )
        except Exception as failure:
            notes("clock", f"unpaced: {failure!r}")
            return Clock(unpaced=repr(failure))
        notes("clock", "written", call)
        clock = Clock(call=call, code=code, written=MachineProvenance.of(call))

    # run again on a reuse: the draft stores the code rather than the verdict,
    # and a subprocess answers this for nothing
    detail = wrong_on(draft.cases, code=clock.code or "", cap_ms=cap_ms)
    if detail is None:
        return clock
    notes("clock", detail)
    # the call is kept, since the site answered and the record is what says
    # what it cost. Nothing is stored, so the draft stops at the step before
    return clock.model_copy(update={"code": None, "unpaced": detail})


def fuzzing(draft: Draft, inputs: Inputs, *, cap_ms: int) -> Fuzzing | None:
    """The pass `harden` runs before its first round, or nothing where no
    generator was written for it to build with."""
    if inputs.built is None or inputs.written is None:
        return None
    return pass_over(
        inputs.built,
        canonical=draft.canonical,
        reference=draft.reference or "",
        written=inputs.written,
        cap_ms=cap_ms,
    )


__all__ = [
    "STEPS",
    "Passage",
    "building",
    "carried",
    "fuzzing",
    "measured",
    "paced",
    "sites",
    "stored",
    "to_agreed",
    "to_built",
    "to_hardened",
    "to_paced",
    "to_searched",
    "write_one",
]
