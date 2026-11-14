import argparse

from climb.cards import CardStore
from climb.matches import Coverage, MatchLog, coverage, uncovered
from climb.solution_claims import load_problems
from climb.solutions import SolutionLog
from climb.storage import Database


def gaps(args: argparse.Namespace, root: Database) -> None:
    covered = coverage(
        CardStore(root).all(),
        load_problems(root),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
    )
    shown = covered if args.all else uncovered(covered)
    if shown:
        width = max(len(one.card_slug) for one in shown)
        for one in shown:
            print(f"{one.card_slug:<{width}}  {line(one)}")
    core = [one for one in covered if not one.optional]
    print(f"{len(uncovered(covered))} of {len(core)} core template(s) carry no solution")


def line(one: Coverage) -> str:
    """The template, and what displays it. A gap says so in words: a count of
    zero reads as a column a reader has to interpret."""
    displaying = f"{len(one.solution_ids)} solution(s)" if one.solution_ids else "no solution"
    return f"{one.template_slug:<28}  {displaying}"
