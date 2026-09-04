import argparse
import sys
from collections import Counter
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.bench import bench as chosen_bench
from algo_coach.cli.display import sampled
from algo_coach.cli.transport import transport
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    BENCH,
    Bench,
    Corpus,
    GenerationResult,
    Held,
    Notes,
    Progress,
    ReplayResult,
    Resumed,
    Step,
    Target,
    replay,
    resume,
    starts_at,
    swept,
    targets,
    write_problems,
)
from algo_coach.matches import MatchLog
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import (
    Call,
    Card,
    Draft,
    MachineProvenance,
    SettledCase,
    SiteOutcome,
    WritingState,
)
from algo_coach.solutions import SolutionLog

# the modes a run can be put in. Each reads its own input and reports its own
# summary, so a run doing two would print both under one
MODES = ("replay", "resume", "drafts", "draft")

# how wide one case prints before it is cut. A separating input runs to
# thousands of elements, and the line is there to identify a case
CASE_WIDTH = 96


def generate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    if len([one for one in MODES if getattr(args, one)]) > 1:
        named = ", ".join(f"--{one}" for one in MODES)
        parser.exit(2, f"generate: {named} each do their own work, so one at a time\n")
    if args.replay:
        return replayed(args, parser, root)
    if args.resume:
        return resumed(args, parser, root)
    if args.drafts:
        return listed(args, parser, root)
    if args.draft:
        return shown(args, parser, root)
    aimed = resolve(args, parser, root)
    api = transport(args, parser)
    calls, corpus = CallLog(root), Corpus.at(root)
    outcomes = OutcomeLog(root)
    bench = chosen_bench(args, parser)

    results = []
    for target in aimed:
        result = write_problems(
            api,
            calls,
            target.card,
            target.template,
            corpus,
            count=args.count,
            bench=bench,
            on_progress=show,
            on_step=stage,
            outcomes=outcomes,
            drafts=DraftStore(root),
        )
        results.append(result)
        for drafted in result.drafted:
            print(written(drafted, code=args.code))
        for one in result.held:
            print(holding(target, one))
        # A broken configuration fails the next template the same way, so the
        # run stops rather than spending its abort count once per gap.
        if result.aborted:
            break

    print(summary(results, aimed, bench))
    if any(result.aborted for result in results):
        parser.exit(1, f"generate: aborted after {ABORT_AFTER} consecutive failures\n")
    failed = any(result.failed for result in results)
    if failed and not any(result.drafted for result in results):
        # not "nothing written": a call that raised leaves the draft the steps
        # before it wrote, and the block above names it
        parser.exit(1, "generate: no problem stored\n")


def resumed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Every held draft carried forward, at the bench the flags name.

    The store is the input rather than a template, so the flags that aim a
    write name nothing here. A rejected draft is terminal and is not among
    them.
    """
    if args.card or args.template or args.gaps:
        parser.exit(2, "generate: --resume reads the stored drafts, so it is aimed at nothing\n")
    drafts = DraftStore(root)
    swept(drafts)
    waiting = [one for one in drafts.all() if one.state is not WritingState.REJECTED]
    if not waiting:
        parser.exit(0, "generate: no draft is waiting on a step\n")

    api = transport(args, parser)
    bench = chosen_bench(args, parser)
    cards = CardStore(root).all()
    calls, corpus = CallLog(root), Corpus.at(root)
    outcomes = OutcomeLog(root)

    results, unaimed = [], 0
    for index, draft in enumerate(waiting, start=1):
        target = written_for(cards, draft)
        if target is None:
            # the form it was briefed on is gone, so nothing says what its
            # search or its ladder would be
            unaimed += 1
            print(f"draft {draft.id}: no template {draft.template_id}", file=sys.stderr)
            continue
        result = resume(
            api,
            calls,
            target.template,
            draft,
            corpus,
            bench=bench,
            notes=Notes(stage, index=index, total=len(waiting)),
            outcomes=outcomes,
            drafts=drafts,
        )
        results.append(result)
        for landed in result.drafted:
            print(written(landed, code=args.code))
        for one in result.held:
            print(holding(target, one))

    print(resume_summary(results, bench, unaimed=unaimed))
    if not any(result.drafted for result in results):
        parser.exit(1, "generate: no problem stored\n")


def listed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Every stored draft, and what a resume at this bench would do with each.

    It makes no call, so what a sweep would spend is readable before it is
    spent. A rejected draft is listed too: its gate is what says why nothing
    resumes it.
    """
    if args.card or args.template or args.gaps:
        parser.exit(2, "generate: --drafts reads the stored drafts, so it is aimed at nothing\n")
    stored = DraftStore(root).all()
    if not stored:
        parser.exit(0, "generate: no draft is stored\n")
    bench = chosen_bench(args, parser)
    cards = CardStore(root).all()
    waiting = [(draft, written_for(cards, draft)) for draft in stored]
    for draft, target in waiting:
        print(listing(draft, target, bench))
    print(drafts_summary(waiting, bench))


def listing(draft: Draft, target: Target | None, bench: Bench) -> str:
    """One stored draft: the form it was briefed on, how far it was written,
    and what it is waiting on."""
    form = target.template.slug if target is not None else str(draft.template_id)
    return f"{draft.id}  {form[:24]:<24}  {draft.state:<10}  {waiting_on(draft, target, bench)}"


def waiting_on(draft: Draft, target: Target | None, bench: Bench) -> str:
    """What a resume would do with this draft. A terminal state names what put
    it there, since no step follows it."""
    if draft.state is WritingState.REJECTED:
        return f"rejected by {draft.gate}"
    if draft.state is WritingState.LANDED:
        return f"landed as {draft.problem_id}, cleared by the next run"
    if target is None:
        # the form its brief named is not seeded, and a search reads `speedup`
        # from it
        return f"no template {draft.template_id}"
    return f"starts at {starts_at(draft, target.template, bench)}"


def drafts_summary(waiting: list[tuple[Draft, Target | None]], bench: Bench = BENCH) -> str:
    """How many drafts a sweep would carry, apart from the ones it would pass
    over, and the configuration it would pay at."""
    resuming = [
        draft
        for draft, target in waiting
        if target is not None and draft.state not in (WritingState.REJECTED, WritingState.LANDED)
    ]
    return f"{len(waiting)} draft(s) stored, {len(resuming)} would resume, {wrote(bench)}"


def shown(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """One stored draft, whole: what each step left and what a resume would do
    with it. The listing names a draft, and this is what reads one.

    It makes no call, as `--drafts` makes none.
    """
    if args.card or args.template or args.gaps:
        parser.exit(2, "generate: --draft names the draft it reads, so it is aimed at nothing\n")
    draft = one_of(DraftStore(root).all(), args.draft, parser)
    print(
        report(
            draft,
            written_for(CardStore(root).all(), draft),
            OutcomeLog(root).for_writing(draft.id),
            chosen_bench(args, parser),
        )
    )


def one_of(stored: list[Draft], wanted: str, parser: argparse.ArgumentParser) -> Draft:
    """The draft that id names, by prefix: an id is 32 hex characters, and a
    debugging read should not need all of them."""
    matched = [draft for draft in stored if draft.id.startswith(wanted)]
    if not matched:
        parser.exit(1, f"generate: no draft {wanted}\n")
    if len(matched) > 1:
        named = ", ".join(draft.id for draft in matched)
        parser.exit(2, f"generate: {wanted} names {len(matched)} drafts: {named}\n")
    return matched[0]


def report(draft: Draft, target: Target | None, outcomes: list[SiteOutcome], bench: Bench) -> str:
    """One draft as a page: where it stands, what each step was written at, the
    problem itself, and what the sites left."""
    return "\n".join(
        [
            f"# {draft.title} ({draft.id})",
            "",
            heading(draft, target),
            waiting_on(draft, target, bench),
            "",
            "## configurations",
            *(f"  {name:<15} {configured(getattr(draft, name))}" for name in Bench.model_fields),
            "",
            "## statement",
            "",
            draft.statement,
            "",
            *cases(draft),
            *listing_code("canonical", draft.canonical),
            *listing_code("reference", draft.reference),
            *listing_code(f"input generator (up to {draft.largest})", draft.builder),
            *sites(outcomes),
        ]
    )


def heading(draft: Draft, target: Target | None) -> str:
    """The form it was briefed on and how far it was written. A technique brief
    names no form, and neither does a draft whose card is gone."""
    form = target.template.slug if target is not None else str(draft.template_id)
    return f"{form}, {draft.difficulty}, {draft.state}"


def configured(written: MachineProvenance | None) -> str:
    """What one step ran at, or that it never ran. The digest too: it is half
    of what a resume compares, and a prompt edit moves it alone."""
    if written is None:
        return "not taken"
    at = sampled(written.temperature)
    return f"{written.model}, effort {written.effort} @{at}, {written.prompt_hash} @ {written.pin}"


def cases(draft: Draft) -> list[str]:
    """The set as the steps left it: what the two solutions settled, what the
    rounds won, and the case the search stored. The declared set stands where
    no reference has settled it yet."""
    if not draft.cases:
        declared = [f"  {shortened(one.args, one.expected)}" for one in draft.declared]
        return ["## cases (declared, unsettled)", *declared, ""]
    separating = [draft.separating] if draft.separating is not None else []
    counted = f"{len(draft.cases)} settled, {len(draft.won)} won, {len(separating)} separating"
    return [
        f"## cases ({counted})",
        *(f"  {settled(one)}" for one in [*draft.cases, *draft.won, *separating]),
        "",
    ]


def settled(case: SettledCase) -> str:
    """One case, and whose answer it carries. The round is what a replay
    rebuilds the set from, so it prints beside the source."""
    return f"{shortened(case.args, case.expected)}  [{case.expected_from}, round {case.round}]"


def shortened(args: object, expected: object) -> str:
    """Arguments and return on one line, cut to a width. A separating input
    runs to thousands of elements, where the line is here to identify a
    case."""
    line = f"{args} -> {expected}"
    return line if len(line) <= CASE_WIDTH else line[: CASE_WIDTH - 1] + "…"


def listing_code(name: str, code: str | None) -> list[str]:
    """One step's code, fenced. A step that never ran says so rather than
    printing an empty block."""
    if code is None:
        return [f"## {name}", "", "not written", ""]
    return [f"## {name}", "", "```python", code.rstrip(), "```", ""]


def sites(outcomes: list[SiteOutcome]) -> list[str]:
    """What each call site left on this writing, in the order they were
    written. A resumed step wrote a second record, so a site can appear
    twice."""
    if not outcomes:
        return ["## sites", "", "none recorded: they are written once the loop has run"]
    return ["## sites", *(f"  {left(one)}" for one in outcomes)]


def left(one: SiteOutcome) -> str:
    """One site outcome: its gate, then the counters that are not zero. Every
    counter would print three zeroes for the sites that carry none."""
    parts = [f"{one.site:<15} {one.model}"]
    if one.gate is not None:
        parts.append(f"gate {one.gate}{f': {one.detail}' if one.detail else ''}")
    for name in ("mutants", "survived", "killed", "won", "offered"):
        if getattr(one, name):
            parts.append(f"{name} {getattr(one, name)}")
    if one.rounds:
        parts.append(f"rounds {one.rounds}")
    if one.separating is not None:
        parts.append(f"separating at {one.separating}")
    if one.unseparated is not None:
        parts.append(f"unseparated: {one.unseparated}")
    return "  ".join(parts)


def written_for(cards: list[Card], draft: Draft) -> Target | None:
    """The card and template a draft was briefed on, by the id it carries."""
    for card in cards:
        for template in card.templates:
            if template.id == draft.template_id:
                return Target(card=card, template=template)
    return None


def resume_summary(results: list[Resumed], bench: Bench = BENCH, *, unaimed: int = 0) -> str:
    """What the resumed drafts became, and where each run started."""
    stored = sum(len(result.drafted) for result in results)
    line = f"{len(results)} draft(s) resumed, {stored} stored, {wrote(bench)}"
    on_hold = sum(len(result.held) for result in results)
    if on_hold:
        line += f", {on_hold} held again"
    failed = sum(len(result.failed) for result in results)
    if failed:
        line += f", {failed} failed"
    if unaimed:
        # apart from a failure: nothing was asked, since the form it names is
        # not among the seeded cards
        line += f", {unaimed} naming no template"
    started = Counter(result.started_at for result in results)
    if started:
        line += ", from " + ", ".join(
            f"{count} at {state}" for state, count in started.most_common()
        )
    return line


def replayed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The answering sites over the stored problems, at the bench the flags
    name.

    The corpus is the input rather than a template, so the flags that aim a
    write name nothing here.
    """
    if args.card or args.template or args.gaps:
        parser.exit(2, "generate: --replay reads the stored corpus, so it is aimed at nothing\n")
    api = transport(args, parser)
    bench = chosen_bench(args, parser)
    result = replay(
        api,
        CallLog(root),
        Corpus.at(root),
        OutcomeLog(root),
        CardStore(root).all(),
        bench=bench,
        limit=args.limit,
        fresh=args.fresh,
        on_step=stage,
    )
    print(replay_summary(result, bench))
    if result.aborted:
        parser.exit(1, f"generate: aborted after {ABORT_AFTER} consecutive failures\n")


def replay_summary(result: ReplayResult, bench: Bench = BENCH) -> str:
    """What the replay paid for, beside what it did not have to."""
    line = f"{result.asked} pair(s) asked, {result.skipped} skipped, {wrote(bench)}"
    if result.unasked:
        # apart from a skip: nothing was there to ask about, at no cost
        line += f", {result.unasked} with nothing to ask"
    if result.failed:
        line += f", {len(result.failed)} failed"
    return line


def summary(results: list[GenerationResult], aimed: list[Target], bench: Bench = BENCH) -> str:
    """What the run stored, over every template it was aimed at."""
    stored = sum(len(result.drafted) for result in results)
    kept = f"{stored} problem(s) stored, {wrote(bench)}"
    if len(aimed) > 1:
        kept += f", over {len(aimed)} template(s)"
    discarded = sum(len(result.discarded) for result in results)
    if discarded:
        # Repeated from the per-problem lines: a run of ten scrolls past them.
        kept += f", {discarded} discarded"
    on_hold = sum(len(result.held) for result in results)
    if on_hold:
        # apart from a discard: the calls are kept and the form still has no
        # problem, which is what the next run is aimed at
        kept += f", {on_hold} held"
    return kept


def holding(target: Target, one: Held) -> str:
    """One draft the run left short of landing, named by the form it was
    written for. It is the gap the next run aims at: the template carries no
    problem until this draft is resumed or rejected."""
    return "\n".join(
        [
            f"\n# held: {one.draft.title} ({target.template.slug}, {one.draft.state})",
            "",
            f"{stopped_by(one)}. Held as draft {one.draft.id}.",
        ]
    )


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


def resolve(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> list[Target]:
    """What the run is written for, resolved before any call: the templates
    carrying no match, or the one named."""
    cards = CardStore(root).all()
    if args.gaps:
        return aimed_at_gaps(args, parser, root, cards)
    if not (args.card and args.template):
        parser.exit(2, "generate: name a --card and a --template, or aim the run with --gaps\n")
    card = next((one for one in cards if one.slug == args.card), None)
    if card is None:
        parser.exit(2, f"generate: no card {args.card!r} — seed it first\n")
    template = next((one for one in card.templates if one.slug == args.template), None)
    if template is None:
        named = ", ".join(one.slug for one in card.templates)
        parser.exit(2, f"generate: no template {args.template!r} on {args.card}: {named}\n")
    return [Target(card=card, template=template)]


def aimed_at_gaps(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    root: Path,
    cards: list[Card],
) -> list[Target]:
    if args.template:
        parser.exit(2, "generate: --gaps names the templates, so --template says nothing\n")
    if args.card and not any(one.slug == args.card for one in cards):
        parser.exit(2, f"generate: no card {args.card!r} — seed it first\n")
    aimed = targets(
        cards,
        ProblemStore(root).all(),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
    )
    if args.card:
        aimed = [one for one in aimed if one.card.slug == args.card]
    if not aimed:
        parser.exit(0, "generate: no gap — every core template carries a solution\n")
    return aimed


def written(draft: Draft, *, code: bool) -> str:
    """One problem as it was written."""
    block = [
        f"\n# {draft.title} ({draft.difficulty}, {len(draft.declared)} case(s))",
        "",
        draft.statement,
    ]
    if code:
        block += ["", "```python", draft.canonical.rstrip(), "```"]
    return "\n".join(block)


def stage(step: Step) -> None:
    """One line per stage, on stderr and flushed as the run goes."""
    print(staged(step), file=sys.stderr, flush=True)


def staged(step: Step) -> str:
    """What a stage is doing and what it left: three calls and a mutation loop
    take minutes, and a line per problem shows none of it."""
    counter = f"[{step.index:>{len(str(step.total))}}/{step.total}]"
    return f"{counter} {step.name:<10} {step.detail}{spent(step.call)}"


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


def show(progress: Progress) -> None:
    """One line per problem, on stderr and flushed: two calls take a minute."""
    counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
    print(
        f"{counter} {progress.template_slug[:24]:<24} {progress.title[:40]:<40}  "
        f"{verdict(progress)}",
        file=sys.stderr,
        flush=True,
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
    return f"{cases}  {progress.outcome}  {landed}{bar(progress)}{timing(progress)}"


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
    won = f", +{progress.won}/{progress.offered} case(s)" if progress.offered else ""
    return f"  kills {killed}/{progress.mutants} ({sources(progress)}){won}"


def sources(progress: Progress) -> str:
    """Where each kill came from, in the order the loop reached them. A source
    that killed nothing still prints, since zero is what says it was tried."""
    rounds = ", ".join(f"{one} round {at}" for at, one in enumerate(progress.caught, start=1))
    return ", ".join(
        part for part in (f"{progress.declared} set", f"{progress.fuzzed} fuzz", rounds) if part
    )


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
