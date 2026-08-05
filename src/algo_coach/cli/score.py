import argparse
from pathlib import Path

from algo_coach.claims import MODEL, PROMPT_VERSION, Score, score_backlog
from algo_coach.cli.client import client
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


def score(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The classifier against the user's own claims. Writes nothing: the
    verdicts are read once and reported, never stored."""
    api = client(args, parser)
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    result = score_backlog(api, log, problems, user_id=args.user, limit=args.limit)

    for failure in result.failed:
        print(f"{failure.attempt_id}: {failure.reason}")
    if not result.scored:
        parser.exit(1, f"score: nothing hand-claimed to score against for {args.user}\n")

    share = result.exact / result.scored
    print(f"{MODEL}, prompt {PROMPT_VERSION}")
    print(f"{result.exact}/{result.scored} exact ({share:.0%})\n")
    print(render(result))

    # Printed in full, not summarised: reading them is how a mislabelled hand
    # claim is caught, and a corrected claim supersedes the earlier one.
    for disagreement in result.disagreements:
        user = " ".join(disagreement.user)
        machine = " ".join(disagreement.machine)
        print(f"\n{disagreement.attempt_id}\n  you: {user}\n  it:  {machine}")


def render(result: Score) -> str:
    """Per technique, since the board is — an overall number hides a code the
    classifier reaches for wrongly everywhere it is read."""
    header = ("technique", "attempts", "exact", "missed", "over")
    body = [
        (row.technique, str(row.attempts), str(row.exact), str(row.missed), str(row.over))
        for row in result.per_technique
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
