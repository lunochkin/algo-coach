"""What a generation run prints: a stage line per step as it goes, a row per
problem, and the block it ends on."""

import sys
from collections import Counter
from collections.abc import Sequence

from algo_coach.cli.display import clipped, counter, progress, sampled
from algo_coach.generation import (
    BENCH,
    Bench,
    Discarded,
    GenerationResult,
    Held,
    Progress,
    ReplayResult,
    Resumed,
    Step,
    Target,
    landing,
)
from algo_coach.schema import (
    Call,
    Draft,
)


def stage(step: Step) -> None:
    """One line per stage, on stderr and flushed as the run goes."""
    print(staged(step), file=sys.stderr, flush=True)


def staged(step: Step) -> str:
    """What a stage is doing and what it left: three calls and a mutation loop
    take minutes, and a line per problem shows none of it."""
    return f"{counter(step.index, step.total)} {step.name:<10} {step.detail}{spent(step.call)}"


def spent(call: Call | None) -> str:
    """What a stage's call cost, where it made one."""
    if call is None:
        return ""
    tokens = f"{count(call.input_tokens)}/{count(call.output_tokens)} tok"
    waited = f"{call.elapsed_ms / 1000:.1f}s" if call.elapsed_ms is not None else "?"
    price = f", ${call.cost:.4f}" if call.cost else ""
    return f"  ({tokens}, {waited}{price})"


def count(tokens: int | None) -> str:
    return "?" if tokens is None else f"{tokens:,}"


def show(one: Progress) -> None:
    progress(
        one.index,
        one.total,
        clipped(one.template_slug, 24),
        clipped(one.title, 40),
        verdict=verdict(one),
    )


def verdict(progress: Progress) -> str:
    """The case run and whether it was kept, apart: a written problem can still
    be discarded."""
    if progress.reason is not None:
        return f"! {progress.reason}"
    cases = f"{progress.cases} case(s)"
    if progress.outcome is None:
        return f"{cases}  not run"
    landed = "landed" if progress.landed else "not stored"
    return (
        f"{cases}  {progress.outcome}  {landed}{declared(progress)}"
        f"{bar(progress)}{timing(progress)}{paid(progress)}"
    )


def declared(progress: Progress) -> str:
    """Cases the canonical answered differently from what its own call
    declared. It rejects nothing, so it prints beside the verdict rather than
    as one."""
    return f"  {progress.misdeclared} misdeclared" if progress.misdeclared else ""


def bar(progress: Progress) -> str:
    """What the mutation loop left: which source killed what, and the cases the
    rounds added. The sources are apart because only the last was paid for, and
    whether a round earns its call is read from that. Silent where the
    canonical yielded no mutant."""
    if progress.unmeasured is not None:
        return f"  unmeasured: {progress.unmeasured}"
    if not progress.mutants:
        return ""
    killed = progress.mutants - progress.survived
    won = (
        f", {progress.offered} case(s) proposed, {progress.won} landed" if progress.offered else ""
    )
    return f"  kills {killed}/{progress.mutants} ({sources(progress)}){won}"


def sources(progress: Progress) -> str:
    """Where each kill came from, in the order the loop reached them. A source
    that killed nothing still prints, since zero is what says it was tried."""
    rounds = ", ".join(f"{one} round {at}" for at, one in enumerate(progress.caught, start=1))
    return ", ".join(
        part for part in (f"{progress.declared} set", f"{progress.fuzzed} fuzz", rounds) if part
    )


def paid(progress: Progress) -> str:
    """What the problem cost, over every call its sites and rounds made. The
    stage lines price one call each, and a row nobody watched live is where the
    total is read."""
    return f"  ${progress.cost:.4f}" if progress.cost is not None else ""


def timing(progress: Progress) -> str:
    """What the inputs site left. Silent where the generator was written and
    the form is its own optimum, since nothing was looked for."""
    if progress.unbuilt is not None:
        return f"  unbuilt: {progress.unbuilt}"
    # checked before the size: a search that proved a separation and stored no
    # case carries both, and printing the size alone would read as a stored one
    if progress.unseparated:
        at = f" at {progress.separating}" if progress.separating is not None else ""
        return f"  no case{at}: {progress.unseparated}"
    return f"  separates at {progress.separating}" if progress.separating is not None else ""


def counted(results: Sequence[GenerationResult], field: str) -> int:
    """How many of one kind the run left, over every template it was aimed at."""
    return sum(len(getattr(result, field)) for result in results)


def tallied(*counts: tuple[int, str]) -> str:
    """The non-zero counts as `, 3 held, 1 failed`, so a summary names only what
    the run reached."""
    return "".join(f", {count} {label}" for count, label in counts if count)


def summary(results: Sequence[GenerationResult], aimed: list[Target], bench: Bench = BENCH) -> str:
    """What the run stored, over every template it was aimed at."""
    kept = f"{counted(results, 'drafted')} problem(s) stored"
    if len(aimed) > 1:
        kept += f", over {len(aimed)} template(s)"
    # the discards repeat the per-problem lines, since a run of ten scrolls past
    # them. A hold is apart from a discard: the calls are kept and the form
    # still has no problem, which is what the next run is aimed at
    kept += tallied(
        (counted(results, "discarded"), "discarded"),
        (counted(results, "held"), "held"),
        (counted(results, "failed"), "failed"),
    )
    # last, since it is one line per site where the sites differ
    return f"{kept}, {wrote(bench)}"


def resume_summary(results: Sequence[Resumed], bench: Bench = BENCH, *, unaimed: int = 0) -> str:
    """What the resumed drafts became, and where each run started."""
    line = f"{len(results)} draft(s) resumed, {counted(results, 'drafted')} stored"
    # naming no template is apart from a failure: nothing was asked, since the
    # form it names is not among the seeded cards
    line += tallied(
        (counted(results, "held"), "held again"),
        (counted(results, "failed"), "failed"),
        (unaimed, "naming no template"),
    )
    started = Counter(result.started_at for result in results)
    if started:
        line += ", from " + ", ".join(
            f"{count} at {state}" for state, count in started.most_common()
        )
    # last, as in `summary`: one line per site where the sites differ
    return f"{line}, {wrote(bench)}"


def replay_summary(result: ReplayResult, bench: Bench = BENCH) -> str:
    """What the replay paid for, beside what it did not have to."""
    line = f"{result.asked} pair(s) asked, {result.skipped} skipped, {wrote(bench)}"
    # unasked is apart from skipped: nothing was there to ask about, at no cost
    return line + tallied((result.unasked, "with nothing to ask"), (len(result.failed), "failed"))


def holding(target: Target, one: Held) -> str:
    """One draft the run left short of landing, named by the form it was
    written for. It is the gap the next run aims at: the template carries no
    problem until this draft is resumed or rejected."""
    form = target.template.slug[:24]
    return f"  {one.draft.id}  {form:<24}  {one.draft.state:<10}  {stopped_by(one)}"


def discarding(target: Target, one: Discarded) -> str:
    """One problem written and not kept. Its gate is on the site outcomes of a
    writing no problem names, so the run is where a reader meets it."""
    return f"  {target.template.slug[:24]:<24}  {one.reason}"


def finale(
    reached: Sequence[tuple[Target, GenerationResult]], closing: str, paid: list[Call]
) -> str:
    """What the run ended with, printed once and after every stage line.

    The statements are not in it. Ten of them scroll the result out of the
    terminal, and `algo-coach problem <id>` is what reads one whole.
    """
    block: list[str] = []
    block += section("stored", [written(one) for _, result in reached for one in result.drafted])
    block += section(
        "held", [holding(target, one) for target, result in reached for one in result.held]
    )
    block += section(
        "discarded",
        [discarding(target, one) for target, result in reached for one in result.discarded],
    )
    # a call that returned nothing, where a discard is a problem that arrived
    # and did not survive its runs. It leaves no draft and no site outcome, so
    # the run is the only place it is named
    block += section(
        "failed",
        [
            f"  {target.template.slug[:24]:<24}  {one.reason}"
            for target, result in reached
            for one in result.failed
        ],
    )
    return "\n".join([*block, closing, spending(paid)])


def section(name: str, lines: list[str]) -> list[str]:
    """One block of the report, absent where the run reached none of it."""
    return [f"# {name}", "", *lines, ""] if lines else []


def spending(paid: list[Call]) -> str:
    """What this run's calls cost, over the ones it appended to the log. A
    provider that priced nothing leaves the field absent, so a run of those
    reports the count alone."""
    priced = [one.cost for one in paid if one.cost is not None]
    tokens = sum(one.output_tokens or 0 for one in paid)
    line = f"{len(paid)} call(s), {tokens:,} output token(s)"
    if priced:
        line += f", ${sum(priced):.4f}"
    return line


def stopped_by(one: Held) -> str:
    """Which step had no answer. A raised call comes first, since it ended the
    writing where the rest let it go on; the others read in the order the steps
    run, so the earliest missing answer is what a reader is told about."""
    if one.failed is not None:
        return f"the call raised: {one.failed}"
    if one.unbuilt is not None:
        return f"no input generator: {one.unbuilt}"
    if one.unpaced is not None:
        return f"no naive solution: {one.unpaced}"
    if one.unseparated is not None:
        # the size where a separation was proved and no case stored it, since
        # printing it alone would read as a case the problem carries
        at = f" at {one.separating}" if one.separating is not None else ""
        return f"no separating case{at}: {one.unseparated}"
    return f"the mutation loop went unmeasured: {one.unmeasured}"


def wrote(bench: Bench) -> str:
    """Which model wrote what. One name where every site shares a
    configuration, and one line per site where they differ."""
    shared = bench.shared
    if shared is not None:
        return f"written by {shared.model}, effort {shared.effort} @{sampled(shared.temperature)}"
    # one line per site: four configurations on one line is a line nobody reads
    # to the end, and what wrote a problem is what a re-run has to name
    return "written by\n" + "\n".join(
        f"  {name} {named(bench, name)}" for name in Bench.model_fields
    )


def named(bench: Bench, site: str) -> str:
    """One site's configuration, the temperature included: two sites on one
    model differ by how they were sampled and by nothing a name shows."""
    one = getattr(bench, site)
    return f"{one.model} at {one.effort} @{sampled(one.temperature)}"


def written(draft: Draft) -> str:
    """One stored problem as a line: what it is, and the id that reads it. The
    case count is the set that landed rather than the one the generator
    declared, since the loop and the search append to it."""
    cases = f"{draft.difficulty}, {len(landing(draft))} case(s)"
    return f"  {draft.problem_id}  {draft.title[:40]:<40}  {cases}"


__all__ = [
    "bar",
    "count",
    "counted",
    "declared",
    "discarding",
    "finale",
    "holding",
    "named",
    "paid",
    "replay_summary",
    "resume_summary",
    "section",
    "show",
    "sources",
    "spending",
    "spent",
    "stage",
    "staged",
    "stopped_by",
    "summary",
    "tallied",
    "timing",
    "verdict",
    "written",
    "wrote",
]
