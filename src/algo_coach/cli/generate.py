import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.transport import transport
from algo_coach.generation import EFFORT, MODEL, Corpus, Draft, Progress, write_problems
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Card, Template


def generate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Write problems for one of a card's templates."""
    api = transport(args, parser)
    card, template = resolve(args, parser, root)

    result = write_problems(
        api,
        CallLog(root),
        card,
        template,
        Corpus.at(root),
        count=args.count,
        on_progress=show,
    )

    for drafted in result.drafted:
        print(written(drafted.draft, code=args.code))
    kept = f"{len(result.drafted)} problem(s) stored, written by {MODEL}, effort {EFFORT}"
    if result.discarded:
        # Reported here as well as per problem: a run of ten scrolls, and what
        # the gates rejected is what a template's brief is judged on.
        kept += f", {len(result.discarded)} discarded"
    print(kept)
    if result.aborted:
        parser.exit(1, f"generate: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.drafted:
        parser.exit(1, "generate: nothing written\n")


def resolve(
    args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path
) -> tuple[Card, Template]:
    """The card and the template the brief is built from.

    Named before the run rather than after a call: a slug nothing was seeded
    under would otherwise cost a request to discover.
    """
    card = next((one for one in CardStore(root).all() if one.slug == args.card), None)
    if card is None:
        parser.exit(2, f"generate: no card {args.card!r} — seed it first\n")
    template = next((one for one in card.templates if one.slug == args.template), None)
    if template is None:
        named = ", ".join(one.slug for one in card.templates)
        parser.exit(2, f"generate: no template {args.template!r} on {args.card}: {named}\n")
    return card, template


def written(draft: Draft, *, code: bool) -> str:
    """One problem as it was written, since nothing stores it yet."""
    block = [
        f"\n# {draft.title} ({draft.difficulty}, {len(draft.cases)} case(s))",
        "",
        draft.statement,
    ]
    if code:
        block += ["", "```python", draft.canonical.rstrip(), "```"]
    return "\n".join(block)


def show(progress: Progress) -> None:
    """A line per problem, on stderr as the other run loops report: two calls
    take a minute, and stdout stays the command's own output."""
    counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
    print(
        f"{counter} {progress.template_slug[:24]:<24} {progress.title[:40]:<40}  "
        f"{verdict(progress)}",
        file=sys.stderr,
        flush=True,
    )


def verdict(progress: Progress) -> str:
    """How the problem went: the case run, and whether it was kept.

    Reported apart, because a written problem can still be discarded — its
    canonical failing the cases it was written with, or the reference
    disagreeing with it. A discard is the whole line, since there is no run to
    report where nothing was kept.
    """
    if progress.reason is not None:
        return f"! {progress.reason}"
    cases = f"{progress.cases} case(s)"
    if progress.outcome is None:
        return f"{cases}  not run"
    return f"{cases}  {progress.outcome}  {'landed' if progress.landed else 'not stored'}"
