"""The hand annotation: which of a card's forms a problem exercises.

The question is the card and the record is the pair. One statement is read
once and judged against every form of the card, and the answer writes a row per
template. The ones the problem does not exercise are included: a reference that
only named matches would score the matcher's "yes" and say nothing about its
"no".

Blind by default. The first pass is where the line gets drawn between
exercising a form and merely admitting it. An annotation made with a verdict in
view records what it reviewed rather than what it read, and `informed_by` names
the calls it saw.
"""

import argparse
from collections.abc import Iterable, Mapping
from pathlib import Path
from textwrap import fill

from algo_coach.cards import CardStore
from algo_coach.cli.prompts import ask_choice
from algo_coach.matches import MatchLog, Question, annotatable, candidates
from algo_coach.mint import user_match
from algo_coach.problems import ProblemStore
from algo_coach.schema import MatchSource, Template, TemplateMatch

WIDTH = 100


def annotate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The matcher's question, answered by hand over sampled problems.

    What the matcher is scored against, so it writes `MatchSource.USER` records
    carrying no configuration: nothing re-derives them, which is what makes
    them stand on read however early they were written.
    """
    cards = CardStore(root).all()
    if args.card and not any(card.slug == args.card for card in cards):
        parser.exit(2, f"annotate: no card {args.card!r} — seed it first\n")

    log = MatchLog(root)
    stored = log.matches()
    pool = annotatable(cards, ProblemStore(root).all(), stored, card=args.card, seed=args.seed)
    if not pool:
        left = f"left to annotate for {args.card}" if args.card else "left to annotate"
        parser.exit(1, f"annotate: nothing {left}\n")

    read = machine_verdicts(stored) if args.verdict else {}

    answered = written = 0
    total = min(args.count, len(pool))
    for index, question in enumerate(pool[: args.count], start=1):
        forms = candidates(question.card)
        print(f"\n{index}/{total}  {question.card.slug}  {question.problem.title}")
        print(wrapped(question.problem.statement))
        # Per question, since the forms are this card's. The cue rather than
        # the code: which form a problem asks for is what is being decided, and
        # the trigger is the field that says it. The slug beside the number
        # because a title is the author's shorthand and the slug is what the
        # record names.
        for number, form in enumerate(forms, start=1):
            print(f"\n  {number} {form.slug} — {form.title}")
            print(wrapped(form.trigger, hanging=True))
        if args.verdict:
            print(read_as(question, forms, read))
        print()

        answer = ask_choice("templates", forms, [], none="no template")
        if answer is None or answer.rest:
            break
        if answer.picked is None:
            continue
        picked = {forms[int(number) - 1].id for number in answer.picked}
        saw = shown(question, forms, read)
        for form in forms:
            log.append(
                user_match(form.id, question.problem.id, matched=form.id in picked, informed_by=saw)
            )
            written += 1
        answered += 1

    print(f"\n{answered} question(s) annotated, {written} record(s) written")


def machine_verdicts(matches: Iterable[TemplateMatch]) -> dict[tuple[str, str], TemplateMatch]:
    """The latest reading per pair, whatever configuration produced it.

    Every configuration's, not one named on the command line: this is shown to
    a reader rather than scored, and which matcher answered is printed beside
    the verdict. A pair the hand has settled is not among them — the reader is
    being shown what a machine read, not what they wrote.
    """
    latest: dict[tuple[str, str], TemplateMatch] = {}
    for match in matches:
        if match.source is not MatchSource.CLASSIFIER:
            continue
        pair = (match.template_id, match.problem_id)
        if pair not in latest or match.created_at >= latest[pair].created_at:
            latest[pair] = match
    return latest


def shown(
    question: Question,
    forms: list[Template],
    read: Mapping[tuple[str, str], TemplateMatch],
) -> list[str]:
    """The calls whose verdicts `read_as` put in front of the annotator.

    One call answers a whole card, so the forms of one question usually name
    the same one; it is listed once. A form no matcher has read showed nothing,
    so it informed nothing.

    Recorded on every pair the answer writes, positive and negative alike. What
    the reader saw is a fact about the sitting rather than about the verdict,
    and the negatives are scored as the positives are.
    """
    seen: list[str] = []
    for form in forms:
        match = read.get((form.id, question.problem.id))
        if match is not None and match.call_id is not None and match.call_id not in seen:
            seen.append(match.call_id)
    return seen


def read_as(
    question: Question,
    forms: list[Template],
    read: Mapping[tuple[str, str], TemplateMatch],
) -> str:
    """What the matcher made of the same pairs, named by the model that
    answered. Shown before the answer, which is the reader's choice and has a
    cost: an annotation made with a verdict in view is no longer independent of
    it, and the agreement it is later scored on measures rather less."""
    lines = []
    for form in forms:
        match = read.get((form.id, question.problem.id))
        if match is not None:
            mark = "yes" if match.matched else "no "
            lines.append(f"  {mark}  {form.slug}  ({match.model})")
    return "\n" + "\n".join(lines) if lines else ""


def wrapped(text: str, *, hanging: bool = False) -> str:
    """A statement or a cue at terminal width. The words are the author's;
    only the wrapping is this reader's."""
    indent = "      " if hanging else "  "
    return "\n".join(
        fill(line, width=WIDTH, initial_indent=indent, subsequent_indent=indent)
        for line in text.splitlines()
        if line.strip()
    )
