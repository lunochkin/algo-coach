"""One stored problem read whole, or the corpus listed.

Its own command rather than a flag on `generate`: a problem outlives the run
that wrote it, and matching, reading and the drill loop all reach it.
"""

import argparse
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.cli.display import configured, left, listing_code, one_of, shortened
from algo_coach.generation import Corpus
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems.techniques import derive
from algo_coach.readings import ReadingLog
from algo_coach.schema import Problem, Solution, TemplateMatch, TestCase


def problem(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The corpus listed, or the one problem an id names."""
    corpus = Corpus.at(root)
    stored = corpus.problems.all()
    if not stored:
        parser.exit(0, "problem: no problem is stored\n")
    if not args.id:
        return listed(stored, corpus, root)
    print(page(one_of(stored, args.id, parser, "problem"), corpus, root))


def listed(stored: list[Problem], corpus: Corpus, root: Path) -> None:
    """Every stored problem: how it stands and what it carries."""
    forms = slugs(root)
    cases = corpus.cases.cases()
    solutions = corpus.solutions.solutions()
    for one in sorted(stored, key=lambda problem: problem.title):
        form = forms.get(one.generated_for or "", str(one.generated_for))
        held = sum(case.problem_id == one.id for case in cases)
        wrote = sum(solution.problem_id == one.id for solution in solutions)
        carries = f"{held} case(s), {wrote} solution(s)"
        print(f"{one.id}  {form[:24]:<24}  {standing(one):<12}  {carries}")
    print(f"{len(stored)} problem(s) stored")


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
    read = derive([one], solutions, ReadingLog(root).readings())[one.id]
    matches = [match for match in corpus.matches.matches() if keyed(match, solutions)]
    return "\n".join(
        [
            f"# {one.title} ({one.id})",
            "",
            f"{forms.get(one.generated_for or '', str(one.generated_for))}, "
            f"{one.difficulty}, {standing(one)}",
            f"techniques: {' '.join(read) or 'none read'}",
            f"written by {configured(one)}",
            "",
            "## statement",
            "",
            one.statement,
            "",
            *cases(corpus.cases.for_problem(one.id)),
            *code(solutions),
            *pairs(matches, solutions, forms),
            *sites(OutcomeLog(root).outcomes(), one.id),
        ]
    )


def slugs(root: Path) -> dict[str, str]:
    """Every seeded template by id, since a problem and a match name one and a
    reader wants the form."""
    return {one.id: one.slug for card in CardStore(root).all() for one in card.templates}


def cases(stored: list[TestCase]) -> list[str]:
    """The set the problem carries, each naming whose answer it holds and the
    round that won it."""
    named = [
        f"  {shortened(one.args, one.expected)}  [{one.expected_from}, round {one.round}]"
        for one in stored
    ]
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


def pairs(
    matches: list[TemplateMatch], solutions: list[Solution], forms: dict[str, str]
) -> list[str]:
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


def sites(outcomes: list, problem_id: str) -> list[str]:
    """What the run that wrote it left, keyed to the problem it landed as."""
    mine = [one for one in outcomes if one.problem_id == problem_id]
    if not mine:
        return ["## sites", "", "none recorded"]
    return ["## sites", *(f"  {left(one)}" for one in mine)]


__all__ = ["problem"]
