import argparse
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.matches import Coverage, MatchLog, coverage, uncovered
from algo_coach.problems import ProblemStore
from algo_coach.solutions import SolutionLog


def gaps(args: argparse.Namespace, root: Path) -> None:
    covered = coverage(
        CardStore(root).all(),
        ProblemStore(root).all(),
        SolutionLog(root).solutions(),
        MatchLog(root).matches(),
    )
    shown = covered if args.all else uncovered(covered)
    if shown:
        width = max(len(one.card_slug) for one in shown)
        for one in shown:
            print(f"{one.card_slug:<{width}}  {line(one)}")
    print(f"{len(uncovered(covered))} of {len(covered)} core template(s) carry no solution")


def line(one: Coverage) -> str:
    """The template, and what displays it. A gap says so in words: a count of
    zero reads as a column a reader has to interpret."""
    displaying = f"{len(one.solution_ids)} solution(s)" if one.solution_ids else "no solution"
    return f"{one.template_slug:<28}  {displaying}"
