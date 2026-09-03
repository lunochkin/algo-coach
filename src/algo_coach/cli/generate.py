import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.bench import bench as chosen_bench
from algo_coach.cli.display import sampled
from algo_coach.cli.transport import transport
from algo_coach.generation import (
    BENCH,
    Bench,
    Corpus,
    Draft,
    GenerationResult,
    Progress,
    ReplayResult,
    Step,
    Target,
    replay,
    targets,
    write_problems,
)
from algo_coach.matches import MatchLog
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Call, Card
from algo_coach.solutions import SolutionLog


def generate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    if args.replay:
        return replayed(args, parser, root)
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
        )
        results.append(result)
        for drafted in result.drafted:
            print(written(drafted.draft, code=args.code))
        # A broken configuration fails the next template the same way, so the
        # run stops rather than spending its abort count once per gap.
        if result.aborted:
            break

    print(summary(results, aimed, bench))
    if any(result.aborted for result in results):
        parser.exit(1, f"generate: aborted after {ABORT_AFTER} consecutive failures\n")
    failed = any(result.failed for result in results)
    if failed and not any(result.drafted for result in results):
        parser.exit(1, "generate: nothing written\n")


def replayed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The answering sites over the stored problems, at the bench the flags name.

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
    return kept


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
        f"\n# {draft.title} ({draft.difficulty}, {len(draft.cases)} case(s))",
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
    """What the mutation loop left: the mutants the set caught, and the cases
    the rounds added. Silent where the canonical yielded no mutant."""
    if progress.unmeasured is not None:
        return f"  unmeasured: {progress.unmeasured}"
    if not progress.mutants:
        return ""
    killed = progress.mutants - progress.survived
    won = f", +{progress.won} case(s)" if progress.won else ""
    return f"  kills {killed}/{progress.mutants}{won}"


def timing(progress: Progress) -> str:
    """What the inputs site left. Silent where the generator was written and
    the form is its own optimum, since nothing was looked for."""
    if progress.unbuilt is not None:
        return f"  unbuilt: {progress.unbuilt}"
    if progress.separating is not None:
        return f"  separates at {progress.separating}"
    return f"  no separation: {progress.unseparated}" if progress.unseparated else ""
