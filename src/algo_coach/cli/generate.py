import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.transport import transport
from algo_coach.generation import (
    EFFORT,
    MODEL,
    Corpus,
    Draft,
    GenerationResult,
    Progress,
    Target,
    targets,
    write_problems,
)
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Card
from algo_coach.solutions import SolutionLog


def generate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    aimed = resolve(args, parser, root)
    api = transport(args, parser)
    calls, corpus = CallLog(root), Corpus.at(root)

    results = []
    for target in aimed:
        result = write_problems(
            api,
            calls,
            target.card,
            target.template,
            corpus,
            count=args.count,
            on_progress=show,
        )
        results.append(result)
        for drafted in result.drafted:
            print(written(drafted.draft, code=args.code))
        # A broken configuration fails the next template the same way, so the
        # run stops rather than spending its abort count once per gap.
        if result.aborted:
            break

    print(summary(results, aimed))
    if any(result.aborted for result in results):
        parser.exit(1, f"generate: aborted after {ABORT_AFTER} consecutive failures\n")
    failed = any(result.failed for result in results)
    if failed and not any(result.drafted for result in results):
        parser.exit(1, "generate: nothing written\n")


def summary(results: list[GenerationResult], aimed: list[Target]) -> str:
    """What the run stored, over every template it was aimed at."""
    stored = sum(len(result.drafted) for result in results)
    kept = f"{stored} problem(s) stored, written by {MODEL}, effort {EFFORT}"
    if len(aimed) > 1:
        kept += f", over {len(aimed)} template(s)"
    discarded = sum(len(result.discarded) for result in results)
    if discarded:
        # Repeated from the per-problem lines: a run of ten scrolls past them.
        kept += f", {discarded} discarded"
    return kept


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
    return f"{cases}  {progress.outcome}  {landed}{timing(progress)}"


def timing(progress: Progress) -> str:
    """What the speedup search left. Silent where the form is its own optimum,
    since nothing was looked for."""
    if progress.separating is not None:
        return f"  separates at {progress.separating}"
    return f"  no separation: {progress.unseparated}" if progress.unseparated else ""
