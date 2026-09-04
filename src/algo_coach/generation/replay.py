"""Re-asking a call site about a problem the store already holds: the three
answering sites over a stored statement, skipping the pairs this configuration
has answered at the digest it would send now.

Read-only over the corpus, for the reason `flows.md` gives.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Configuration, Transport
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import reference
from algo_coach.generation.blind import request_hash as blind_hash
from algo_coach.generation.checks import CAP_MS
from algo_coach.generation.discrimination import request_hash as discrimination_hash
from algo_coach.generation.hardening import harden, standing
from algo_coach.generation.inputs import builder
from algo_coach.generation.inputs import request_hash as inputs_hash
from algo_coach.generation.landing import Corpus
from algo_coach.generation.run import make
from algo_coach.generation.speedup import DRILL_CAP_MS, Missing, search
from algo_coach.generation.steps import Notes, Step
from algo_coach.generation.writing import Writing
from algo_coach.outcomes import OutcomeLog, answered
from algo_coach.runner import verify
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import (
    Call,
    CallSite,
    Card,
    CaseOutcome,
    CaseResult,
    Discard,
    MachineProvenance,
    Problem,
    ProblemStatus,
    SiteOutcome,
    SolutionRole,
    Template,
    TestCase,
)

# the three sites a stored problem can be re-asked about. The generator writes
# a problem rather than answering one, so asking it again is `generate`
REPLAYED = (CallSite.BLIND, CallSite.DISCRIMINATION, CallSite.INPUTS)


class Failed(BaseModel):
    problem_id: str
    site: CallSite
    reason: str


class ReplayResult(BaseModel):
    asked: int = 0  # pairs a call was paid for
    skipped: int = 0  # pairs this configuration had already answered
    unasked: int = 0  # pairs with nothing to ask about, at no cost
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False


@dataclass(frozen=True)
class Subject:
    """One stored problem and the parts a site is re-asked against."""

    problem: Problem
    canonical: str
    reference: str
    # the clock the search times against, absent on a problem whose template
    # claims no speedup and on one landed before the role existed
    naive: str | None
    cases: list[TestCase]
    template: Template | None  # absent where the brief named a technique

    @property
    def declared(self) -> list[TestCase]:
        """The set the first round's survivors were decided against: what the
        statement was written with, and what the fuzz pass kept. A later
        round's own cases and the separating one were not there, and a loop
        shown them decides other survivors and sends another digest."""
        return [one for one in self.cases if one.round == 0]


@dataclass(frozen=True)
class Asked:
    """What one site's replay left. `call` is absent where it was not asked."""

    call: Call | None = None
    verdicts: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False


def subjects(corpus: Corpus, cards: Iterable[Card]) -> list[Subject]:
    """The problems a site can be re-asked about: served, and carrying both
    roles and the cases that decide them.

    A retired problem is excluded, for the reason `flows.md` gives.
    """
    forms = {one.id: one for card in cards for one in card.templates}
    solutions = corpus.solutions.solutions()
    cases = corpus.cases.cases()
    found = []
    for problem in corpus.problems.all():
        if problem.status is ProblemStatus.RETIRED:
            continue
        mine = [one for one in solutions if one.problem_id == problem.id]
        canonical = next((one for one in mine if one.role is SolutionRole.CANONICAL), None)
        blind = next((one for one in mine if one.role is SolutionRole.REFERENCE), None)
        slow = next((one for one in mine if one.role is SolutionRole.NAIVE), None)
        theirs = [one for one in cases if one.problem_id == problem.id]
        if canonical is None or blind is None or not theirs:
            continue
        found.append(
            Subject(
                problem=problem,
                canonical=canonical.code,
                reference=blind.code,
                naive=slow.code if slow is not None else None,
                cases=theirs,
                template=forms.get(problem.generated_for or ""),
            )
        )
    return found


def replay(
    transport: Transport,
    calls: CallLog,
    corpus: Corpus,
    outcomes: OutcomeLog,
    cards: Iterable[Card],
    *,
    bench: Bench = BENCH,
    cap_ms: int = CAP_MS,
    limit: int | None = None,
    fresh: bool = False,
    on_step: Callable[[Step], None] | None = None,
) -> ReplayResult:
    """Each site over each stored problem, at the bench's configuration.

    `fresh` asks again where a record answers the same prompt, which is what
    measuring a reader against itself needs. `ABORT_AFTER` counts consecutive
    failures, as a generation run does: a broken configuration fails every
    problem the same way.
    """
    asking = subjects(corpus, cards)[:limit]
    result = ReplayResult()
    consecutive = 0
    stored = outcomes.outcomes()

    for index, subject in enumerate(asking, start=1):
        notes = Notes(on_step, index=index, total=len(asking))
        for site in REPLAYED:
            left: list[SiteOutcome] = []
            writing = Writing(template_id=problem_template(subject), into=left)
            try:
                asked = ASK[site](transport, calls, subject, stored, bench, cap_ms, fresh, notes)
            except Exception as failure:
                result.failed.append(
                    Failed(problem_id=subject.problem.id, site=site, reason=repr(failure))
                )
                notes(site, f"failed: {failure!r}")
                consecutive += 1
                if consecutive == ABORT_AFTER:
                    result.aborted = True
                    return result
                continue

            consecutive = 0
            if asked.skipped:
                result.skipped += 1
                continue
            if asked.call is None:
                result.unasked += 1
                continue
            writing(site, asked.call, **asked.verdicts)
            for one in left:
                outcomes.append(one.model_copy(update={"problem_id": subject.problem.id}))
            stored = [*stored, *left]
            result.asked += 1
    return result


def problem_template(subject: Subject) -> str | None:
    return subject.template.id if subject.template else None


def blind_replay(
    transport: Transport,
    calls: CallLog,
    subject: Subject,
    stored: Sequence[SiteOutcome],
    bench: Bench,
    cap_ms: int,
    fresh: bool,
    notes: Notes,
) -> Asked:
    """A second reading of the statement, settled against the cases the problem
    already carries rather than against the canonical it was written with."""
    configuration = bench.blind
    digest = blind_hash(subject.problem.statement)
    if not fresh and asked_already(stored, CallSite.BLIND, subject, configuration, digest):
        notes("blind", "answered at this digest")
        return Asked(skipped=True)

    notes("blind", "writing the reference from the statement alone")
    solution, call = reference(
        transport, calls, subject.problem.statement, configuration=configuration
    )
    verdicts = graded(verify(solution, subject.cases, cap_ms=cap_ms))
    notes("blind", verdicts.get("detail") or "agrees on every case", call)
    return Asked(call=call, verdicts=verdicts)


def graded(results: Sequence[CaseResult]) -> dict[str, Any]:
    """The gate a replayed reference met. A case it could not compute is the
    ordinary path beyond its reach, and computing none of them is not."""
    computed = [one for one in results if one.outcome in (CaseOutcome.PASSED, CaseOutcome.WRONG)]
    if not computed:
        return {"gate": Discard.UNTESTED, "detail": "computed no case"}
    wrong = [one for one in computed if one.outcome is CaseOutcome.WRONG]
    if wrong:
        return {"gate": Discard.DISAGREED, "detail": f"disagrees on {len(wrong)} case(s)"}
    return {}


def discrimination_replay(
    transport: Transport,
    calls: CallLog,
    subject: Subject,
    stored: Sequence[SiteOutcome],
    bench: Bench,
    cap_ms: int,
    fresh: bool,
    notes: Notes,
) -> Asked:
    """The mutation loop over the stored canonical. The survivors are in the
    prompt, so they are computed before the digest can be known."""
    configuration = bench.discrimination
    alive = standing(subject.canonical, subject.declared, cap_ms=cap_ms)
    if not alive:
        notes("mutants", "the stored cases kill every mutant")
        return Asked()

    digest = discrimination_hash(
        subject.problem.statement,
        subject.canonical,
        alive,
        [one.args for one in subject.declared],
    )
    if not fresh and asked_already(stored, CallSite.DISCRIMINATION, subject, configuration, digest):
        notes("mutants", "answered at this digest")
        return Asked(skipped=True)

    hardened = harden(
        transport,
        calls,
        subject.problem.statement,
        canonical=subject.canonical,
        reference=subject.reference,
        cases=subject.declared,
        cap_ms=cap_ms,
        configuration=configuration,
        notes=notes,
    )
    return Asked(
        call=hardened.call,
        verdicts={
            "gate": None if hardened.disagreement is None else Discard.DISAGREED,
            "mutants": hardened.mutants,
            "survived": hardened.survived,
            "won": len(hardened.cases),
            "offered": hardened.offered,
        },
    )


def inputs_replay(
    transport: Transport,
    calls: CallLog,
    subject: Subject,
    stored: Sequence[SiteOutcome],
    bench: Bench,
    cap_ms: int,
    fresh: bool,
    notes: Notes,
) -> Asked:
    """The input builder and the search it feeds. Asked only where the template
    claims a speedup, where the landing path builds for every problem: a replay
    records what a site's answer was judged by, and without a search there is
    no verdict on the code this call wrote."""
    if subject.template is None or not subject.template.speedup:
        return Asked()
    if subject.naive is None:
        # a problem landed before the clock was stored with it. The site's own
        # answer would be judged by a search that cannot run
        notes("timing", "no naive solution stored")
        return Asked()
    configuration = bench.inputs
    digest = inputs_hash(subject.problem.statement)
    if not fresh and asked_already(stored, CallSite.INPUTS, subject, configuration, digest):
        notes("timing", "answered at this digest")
        return Asked(skipped=True)

    notes("timing", "writing the input generator")
    built, call = builder(transport, calls, subject.problem.statement, configuration=configuration)
    found = search(
        make(built.code, cap_ms),
        canonical=subject.canonical,
        naive=subject.naive,
        reference=subject.reference,
        written=MachineProvenance.of(call),
        cap_ms=DRILL_CAP_MS,
        largest=built.largest,
        measure_ms=cap_ms,
    )
    notes(
        "timing",
        f"separates at {found.size}" if found.found else f"no separation: {found.missing}",
        call,
    )
    return Asked(
        call=call,
        verdicts={
            "gate": Discard.DISAGREED if found.missing is Missing.DISAGREED else None,
            "separating": found.size,
            "unseparated": found.missing,
        },
    )


def asked_already(
    stored: Sequence[SiteOutcome],
    site: CallSite,
    subject: Subject,
    configuration: Configuration,
    digest: str,
) -> bool:
    return answered(
        stored,
        site=site,
        problem_id=subject.problem.id,
        configuration=configuration,
        prompt_hash=digest,
    )


ASK = {
    CallSite.BLIND: blind_replay,
    CallSite.DISCRIMINATION: discrimination_replay,
    CallSite.INPUTS: inputs_replay,
}


__all__ = ["REPLAYED", "Asked", "Failed", "ReplayResult", "Subject", "replay", "subjects"]
