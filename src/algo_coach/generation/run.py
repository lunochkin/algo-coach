"""Writing several problems for one template, one after another. Sequential
where the matcher is parallel — `flows.md` gives why."""

from collections.abc import Callable, Sequence

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.drafts import DraftStore
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.checks import (
    CAP_MS,
)
from algo_coach.generation.drafting import cleared, held, moved, swept
from algo_coach.generation.generator import (
    written_for,
)
from algo_coach.generation.landing import Corpus, land
from algo_coach.generation.passage import Passage, carried, write_one
from algo_coach.generation.resuming import starts_at
from algo_coach.generation.steps import SILENT, Notes, Step
from algo_coach.generation.verdicts import why
from algo_coach.generation.writing import Writing
from algo_coach.outcomes import OutcomeLog
from algo_coach.runs import Bounded, as_answered
from algo_coach.schema import (
    Call,
    Card,
    CaseOutcome,
    Discard,
    Draft,
    SiteOutcome,
    Template,
    WritingState,
)


class Failed(BaseModel):
    """One problem that was asked for and did not arrive."""

    index: int
    reason: str


class Discarded(BaseModel):
    """One problem that was written and did not survive its runs. Apart from
    `Failed`, which is a call that returned nothing."""

    index: int
    discard: Discard  # which gate rejected it
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
    # cases the canonical answered differently from what its own call declared
    misdeclared: int = 0
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
    # what this problem's calls cost, over every site and every round. Absent
    # where the provider priced none of them
    cost: float | None = None


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
    unpaced: str | None = None  # no naive solution, so the search had no clock
    unmeasured: str | None = None  # the round's call failed
    # a call that raised, which ends the writing where the others answer
    # nothing and let it go on. The draft the run wrote before it stands
    failed: str | None = None


class GenerationResult(BaseModel):
    drafted: list[Draft] = Field(default_factory=list)
    # written whole and demonstrating nothing, so held until a resume separates
    # it, the template's `speedup` is corrected, or it is rejected
    held: list[Held] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False


class Resumed(GenerationResult):
    """One draft carried forward: the same three ends a written one reaches,
    and the step this run started at."""

    started_at: WritingState


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
    # one recorder per problem, filled as the sites answer and stored once the
    # problem's fate is known, which is the first point there is an id to name
    writings = [(index, Writing(template_id=template.id, into=[])) for index in range(1, count + 1)]

    def ask(item: tuple[int, Writing]) -> Passage:
        index, writing = item
        return write_one(
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

    # one at a time: each call is shown the statements the ones before it wrote
    answers = Bounded(as_answered(ask, writings, concurrency=1))
    # the tail this problem appends, which is what its row is priced over
    paid = len(calls.appended)
    for index, (_, writing), passage, failure in answers:
        records = writing.into or []
        if failure is not None:
            # broad on purpose: a refusal, a rate limit or a reply that does
            # not parse costs this problem and not the run
            raised(
                result,
                failure,
                index=index,
                writing=writing,
                records=records,
                outcomes=outcomes,
                drafts=drafts,
            )
            if on_progress is not None:
                on_progress(
                    Progress(
                        index=index,
                        total=count,
                        template_slug=template.slug,
                        reason=repr(failure),
                        cost=priced(calls.appended[paid:]),
                    )
                )
            paid = len(calls.appended)
            continue

        assert passage is not None  # `as_answered` yields an answer or a failure
        written.append(passage.draft.statement)
        finished(result, corpus, passage, index=index, records=records, outcomes=outcomes)
        p = passage
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index,
                    total=count,
                    template_slug=template.slug,
                    title=p.draft.title,
                    cases=len(p.draft.declared),
                    outcome=p.checked.outcome,
                    misdeclared=len(p.checked.misdeclarations),
                    landed=p.draft.state is WritingState.LANDED,
                    reason=None if p.checked.survived else why(p.checked),
                    separating=p.inputs.separating,
                    unseparated=p.inputs.unseparated,
                    unbuilt=p.inputs.unbuilt,
                    mutants=p.bar.mutants,
                    survived=p.bar.survived,
                    won=p.bar.won,
                    offered=p.bar.offered,
                    built=p.bar.built,
                    kept=p.bar.kept,
                    declared=p.bar.declared,
                    fuzzed=p.bar.fuzzed,
                    caught=p.bar.caught,
                    unmeasured=p.bar.unmeasured,
                    cost=priced(calls.appended[paid:]),
                )
            )
        paid = len(calls.appended)
    result.aborted = answers.aborted
    return result


def raised(
    result: GenerationResult,
    failure: Exception,
    *,
    index: int,
    writing: Writing,
    records: list[SiteOutcome],
    outcomes: OutcomeLog | None,
    drafts: DraftStore | None,
) -> None:
    """A call that raised. The site records the steps before it left are kept,
    and the draft they wrote is read back rather than returned: the exception
    carried none, and what was written is in the store."""
    result.failed.append(Failed(index=index, reason=repr(failure)))
    record(outcomes, records)
    stopped_at = drafts.get(writing.id) if drafts is not None else None
    if stopped_at is not None:
        result.held.append(Held(index=index, draft=stopped_at, failed=repr(failure)))


def finished(
    result: GenerationResult,
    corpus: Corpus,
    p: Passage,
    *,
    index: int,
    records: list[SiteOutcome],
    outcomes: OutcomeLog | None,
) -> None:
    """What one draft ends as: landed, held short of it, or discarded. Shared
    with a resume, which reaches the same three ends by the same rules."""
    gate = p.checked.discard
    if gate is not None:
        record(outcomes, records)
        result.discarded.append(Discarded(index=index, discard=gate, reason=why(p.checked)))
    elif p.draft.state is not WritingState.HARDENED:
        # every gate that judges the problem passed, and a step of the writing
        # did not: held where it stopped rather than landed
        record(outcomes, records)
        result.held.append(
            Held(
                index=index,
                draft=p.draft,
                separating=p.inputs.separating,
                unseparated=p.inputs.unseparated,
                unbuilt=p.inputs.unbuilt,
                unpaced=p.clock.unpaced,
                unmeasured=p.bar.unmeasured,
            )
        )
    else:
        problem = land(corpus, p.template, p.draft)
        # named before it is cleared: a crash between the two then leaves a
        # draft the next run clears rather than a problem written twice
        p.draft = held(p.drafts, moved(p.draft, WritingState.LANDED, problem_id=problem.id))
        cleared(p.drafts, p.draft)
        record(outcomes, records, problem_id=problem.id)
        result.drafted.append(p.draft)


def resume(
    transport: Transport,
    calls: CallLog,
    template: Template,
    draft: Draft,
    corpus: Corpus,
    *,
    bench: Bench = BENCH,
    cap_ms: int = CAP_MS,
    notes: Notes = SILENT,
    outcomes: OutcomeLog | None = None,
    drafts: DraftStore | None = None,
) -> Resumed:
    """One stored draft carried forward, from the first step whose
    configuration or digest moved and otherwise from the one it never took.

    A resume never serves: landing is the only way into `created`, and it still
    requires every gate the writing requires.
    """
    if draft.state is WritingState.REJECTED:
        raise ValueError("a rejected draft is not resumed: its gate said the answer was wrong")
    start = starts_at(draft, template, bench)
    notes("resume", f"starting at {start}")
    # the draft's own id, so a resumed step's site outcome groups with the
    # records of the writing it continues
    records: list[SiteOutcome] = []
    writing = Writing(template_id=template.id, into=records, id=draft.id)
    result = Resumed(started_at=start)
    passage = Passage(
        transport,
        calls,
        template,
        draft,
        start,
        bench=bench,
        cap_ms=cap_ms,
        notes=notes,
        drafts=drafts,
    )
    try:
        # the generator wrote nothing here, so its site records nothing
        carried(passage, writing, generator=None)
    except Exception as failure:
        raised(
            result,
            failure,
            index=1,
            writing=writing,
            records=records,
            outcomes=outcomes,
            drafts=drafts,
        )
        return result
    finished(result, corpus, passage, index=1, records=records, outcomes=outcomes)
    return result


def record(
    outcomes: OutcomeLog | None, left: list[SiteOutcome], *, problem_id: str | None = None
) -> None:
    """Appended after landing, since only then is there a problem to name. The
    `writing_id` groups them either way, which is what a discarded draft
    has."""
    if outcomes is None:
        return
    for outcome in left:
        outcomes.append(outcome.model_copy(update={"problem_id": problem_id}))


def priced(paid: Sequence[Call]) -> float | None:
    """What a problem's calls cost. Absent rather than zero where a provider
    priced none of them, as the run's own summary reports the count alone."""
    costs = [one.cost for one in paid if one.cost is not None]
    return sum(costs) if costs else None


__all__ = [
    "Discarded",
    "Failed",
    "GenerationResult",
    "Held",
    "Progress",
    "Resumed",
    "finished",
    "priced",
    "raised",
    "record",
    "resume",
    "write_problems",
]
