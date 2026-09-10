"""One stored problem read whole, or the corpus listed.

Its own command rather than a flag on `generate`: a problem outlives the run
that wrote it, and matching, solution claims and the drill loop all reach it.
"""

import argparse
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.cli.display import (
    case_line,
    configured,
    listing_code,
    one_of,
    sites,
)
from algo_coach.generation import Corpus
from algo_coach.outcomes import OutcomeLog
from algo_coach.schema import Problem, RetirementReason, Solution, TemplateMatch, TestCase
from algo_coach.solution_claims import SolutionClaimLog, derive


def problem(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The corpus listed, or the one problem an id names."""
    corpus = Corpus.at(root)
    stored = corpus.problems.all()
    if not stored:
        parser.exit(0, "problem: no problem is stored\n")
    if args.retire:
        return retired_by_hand(args, parser, stored, corpus, root)
    if not args.id:
        return listed(stored, corpus, root)
    print(page(one_of(stored, args.id, parser, "problem"), corpus, root))


def retired_by_hand(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    stored: list[Problem],
    corpus: Corpus,
    root: Path,
) -> None:
    """The problem read whole, then retired as `defective` once the reader says
    so. Every user is served it, so the loop never retires one."""
    if args.id:
        parser.exit(2, "problem: --retire names the problem it retires\n")
    one = one_of(stored, args.retire, parser, "problem")
    if not one.served:
        parser.exit(0, f"problem {one.id}: already {standing(one)}\n")
    print(page(one, corpus, root))
    try:
        answer = input(f"retire {one.id} as defective? [y/N]: ").strip().lower()
    except EOFError:
        answer = ""
    if answer != "y":
        parser.exit(0, "problem: nothing retired\n")
    left = corpus.problems.retire(one.id, RetirementReason.DEFECTIVE)
    print(f"problem {left.id}: {standing(left)}")


def listed(stored: list[Problem], corpus: Corpus, root: Path) -> None:
    """Every stored problem: how it stands and what it carries."""
    forms = slugs(root)
    cases = corpus.cases.cases()
    solutions = corpus.solutions.solutions()
    for one in sorted(stored, key=lambda problem: problem.title):
        form = aimed_at(one, forms)
        held = sum(case.problem_id == one.id for case in cases)
        wrote = sum(solution.problem_id == one.id for solution in solutions)
        carries = f"{held} case(s), {wrote} solution(s)"
        print(f"{one.id}  {form[:24]:<24}  {standing(one):<12}  {carries}")
    print(f"{len(stored)} problem(s) stored")


def aimed_at(one: Problem, forms: dict[str, str]) -> str:
    """The target, as a reader names it: the template's slug, or the
    technique."""
    if one.target_template_id is not None:
        return forms.get(one.target_template_id, one.target_template_id)
    return one.target_technique or "no target"


def standing(one: Problem) -> str:
    """Its status, and the reason where one retired it: readers treat the two
    retirements apart."""
    if one.retired_reason is not None:
        return f"{one.status}: {one.retired_reason}"
    return str(one.status)


def page(one: Problem, corpus: Corpus, root: Path) -> str:
    """One problem as a page: what it asks, the cases that decide it, every
    solution written for it, and what the run that wrote it left."""
    forms = slugs(root)
    solutions = corpus.solutions.for_problem(one.id)
    read = derive([one], solutions, SolutionClaimLog(root).claims())[one.id]
    matches = [match for match in corpus.matches.matches() if keyed(match, solutions)]
    return "\n".join(
        [
            f"# {one.title} ({one.id})",
            "",
            f"{aimed_at(one, forms)}, {one.difficulty}, {standing(one)}",
            f"techniques: {' '.join(read) or 'none read'}",
            f"written by {configured(one)}",
            "",
            "## statement",
            "",
            one.statement,
            "",
            *cases(corpus.cases.for_problem(one.id)),
            *code(solutions),
            *pairs(matches, forms),
            *sites(OutcomeLog(root).for_problem(one.id), none="none recorded"),
        ]
    )


def slugs(root: Path) -> dict[str, str]:
    """Every seeded template by id, since a problem and a match name one and a
    reader wants the form."""
    return {one.id: one.slug for card in CardStore(root).all() for one in card.templates}


def cases(stored: list[TestCase]) -> list[str]:
    """The set the problem carries, each naming whose answer it holds and the
    round that won it."""
    named = [f"  {case_line(one)}" for one in stored]
    return [f"## cases ({len(stored)})", *named, ""]


def code(solutions: list[Solution]) -> list[str]:
    """Every solution, headed by its role and the configuration that wrote it.
    Several canonicals is the ordinary case."""
    block: list[str] = []
    for one in solutions:
        block += [f"### {one.role} ({one.id})", "", f"{configured(one)}", ""]
        block += listing_code(one.role, one.code)[1:]
    return ["## solutions", "", *block] if block else ["## solutions", "", "none stored", ""]


def keyed(match: TemplateMatch, solutions: list[Solution]) -> bool:
    return any(match.solution_id == one.id for one in solutions)


def pairs(matches: list[TemplateMatch], forms: dict[str, str]) -> list[str]:
    """Which of a card's templates each solution displays. A form is displayed
    by code, so the pair names the solution rather than the problem."""
    if not matches:
        return ["## matches", "", "none stored", ""]
    named = [
        f"  {forms.get(one.template_id, one.template_id)[:24]:<24}  "
        f"{'displays' if one.matched else 'does not'}  {one.source}  {one.solution_id}"
        for one in matches
    ]
    return ["## matches", *named, ""]


__all__ = ["problem"]
