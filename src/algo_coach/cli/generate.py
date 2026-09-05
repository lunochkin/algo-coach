import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.bench import bench as chosen_bench
from algo_coach.cli.display import one_of
from algo_coach.cli.draft import drafts_summary, listing, report
from algo_coach.cli.generating import (
    finale,
    replay_summary,
    resume_summary,
    show,
    stage,
    summary,
)
from algo_coach.cli.transport import transport
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    Corpus,
    GenerationResult,
    Notes,
    Target,
    replay,
    resume,
    swept,
    targets,
    write_problems,
)
from algo_coach.matches import MatchLog
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import load_problems
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import (
    Card,
    Draft,
    WritingState,
)
from algo_coach.solutions import SolutionLog

# the modes a run can be put in. Each reads its own input and reports its own
# summary, so a run doing two would print both under one
MODES = ("replay", "resume", "drafts", "draft")


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

    # the log as the run found it, so what this run paid is the tail past it
    before = len(calls.all())
    reached: list[tuple[Target, GenerationResult]] = []
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
        reached.append((target, result))
        # A broken configuration fails the next template the same way, so the
        # run stops rather than spending its abort count once per gap.
        if result.aborted:
            break

    results = [result for _, result in reached]
    print(finale(reached, summary(results, aimed, bench), calls.all()[before:]))
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

    before = len(calls.all())
    reached: list[tuple[Target, GenerationResult]] = []
    unaimed = 0
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
        reached.append((target, result))

    results = [result for _, result in reached]
    closing = resume_summary(results, bench, unaimed=unaimed)
    print(finale(reached, closing, calls.all()[before:]))
    if not any(result.drafted for result in results):
        parser.exit(1, "generate: no problem stored\n")


def listed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The drafts a sweep would carry, and what a resume at this bench would do
    with each.

    It makes no call, so what a sweep would spend is readable before it is
    spent. A rejected draft is terminal, so it is counted and not listed:
    `--all` prints it, and its gate is what says why nothing resumes it.
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
        if args.all or draft.state is not WritingState.REJECTED:
            print(listing(draft, target, bench))
    print(drafts_summary(waiting, bench, listed=args.all))


def shown(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """One stored draft, whole: what each step left and what a resume would do
    with it. The listing names a draft, and this is what reads one.

    It makes no call, as `--drafts` makes none.
    """
    if args.card or args.template or args.gaps:
        parser.exit(2, "generate: --draft names the draft it reads, so it is aimed at nothing\n")
    draft = one_of(DraftStore(root).all(), args.draft, parser, "draft")
    print(
        report(
            draft,
            written_for(CardStore(root).all(), draft),
            OutcomeLog(root).for_writing(draft.id),
            chosen_bench(args, parser),
        )
    )


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
        load_problems(root),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
    )
    if args.card:
        aimed = [one for one in aimed if one.card.slug == args.card]
    if not aimed:
        parser.exit(0, "generate: no gap — every core template carries a solution\n")
    return aimed


def written_for(cards: list[Card], draft: Draft) -> Target | None:
    """The card and template a draft was briefed on, by the id it carries."""
    for card in cards:
        for template in card.templates:
            if template.id == draft.template_id:
                return Target(card=card, template=template)
    return None
