import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import (
    DEFAULT,
    Comparison,
    Configuration,
    Score,
    TechniqueScore,
    score_backlog,
)
from algo_coach.claims.run import ABORT_AFTER
from algo_coach.cli.classify import show
from algo_coach.cli.transport import transport
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


class Named(argparse.Action):
    """`--model`, `--effort` and `--provider` alternately, into one ordered list.

    One action over three flags, because separate `append` destinations would
    lose which effort followed which model — and the command line's order is
    the output's. A model opens a configuration at the defaults; an effort or a
    provider sets the one just opened, or opens one at the default model coming
    first.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        named: list[list[str]] = getattr(namespace, self.dest, None) or []
        if option_string == "--model":
            named.append([str(value), "", ""])
        else:
            slot = 1 if option_string == "--effort" else 2
            if not named:
                named.append([DEFAULT.model, "", ""])
            if named[-1][slot]:
                parser.exit(2, f"score: two {option_string} for one --model\n")
            named[-1][slot] = str(value)
        setattr(namespace, self.dest, named)


def configurations(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> tuple[Configuration, ...]:
    """The classifiers this run scores, the built-in one when none was named."""
    named = getattr(args, "named", None)
    if not named:
        return (DEFAULT,)
    built = tuple(
        Configuration(
            model=model,
            effort=effort or DEFAULT.effort,
            # A provider carries some models and not others, so the built-in
            # pin belongs to the built-in model alone. Any other model named
            # without one is left to the router, which `require_parameters`
            # already keeps inside the providers that can answer it.
            provider=provider or (DEFAULT.provider if model == DEFAULT.model else None),
        )
        for model, effort, provider in named
    )
    if len(set(built)) != len(built):
        # Reading one configuration twice would measure its own sampling noise,
        # which nothing here consumes yet — refused rather than paid for.
        parser.exit(2, "score: the same configuration named twice\n")
    return built


def score(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The classifier against the user's own claims. Every reading is stored,
    so a later run is paid for only where this one did not reach."""
    if args.stored and args.limit is not None:
        parser.exit(2, "score: --stored with --limit — a cap on a run that pays for nothing\n")
    named = configurations(args, parser)

    # No credentials asked for by a run that makes no call: being runnable
    # anywhere is what makes the stored mode the reproducible one.
    api = None if args.stored else transport(args, parser)
    log = AttemptLog(root)
    calls = CallLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    result = score_backlog(
        api,
        log,
        calls,
        problems,
        user_id=args.user,
        configurations=named,
        concurrency=args.concurrency,
        fresh=args.fresh,
        limit=0 if args.stored else args.limit,
        on_configuration=announce if len(named) > 1 else None,
        on_progress=show,
    )

    # Failures are not printed here: `show` already reported each one as it
    # happened, and which configuration it came from is the header `announce`
    # prints above it. A second list on stdout would say it twice.
    if not result.eval_set:
        parser.exit(1, f"score: nothing hand-claimed to score against for {args.user}\n")
    aborted = [
        name
        for name, scored in zip(labels(named), result.scores, strict=True)
        if scored.score.aborted
    ]
    if aborted:
        # Before the numbers rather than after: what a configuration read
        # before it broke is a slice of the eval set, and a share over it would
        # be read as its answer.
        parser.exit(
            1,
            f"score: {', '.join(aborted)} aborted after {ABORT_AFTER} consecutive failures\n",
        )
    if not result.common:
        # Told apart from the above: ground truth exists and no reading of it
        # does — a stored run before anything was read, or every call failing.
        parser.exit(1, "score: nothing every configuration named has read\n")

    if len(result.scores) == 1:
        alone(result)
    else:
        compared(result)


def alone(result: Comparison) -> None:
    """One configuration: what it read, and every disagreement with the user."""
    only = result.scores[0].score
    print(describe(result.scores[0].configuration))
    print(exactly(only))
    if only.decisions:
        print(decided(only))
    print(f"{only.read} read, {only.reused} reused")
    if only.undecided:
        # Beside the share, since declining shrinks the denominator and
        # improves the number for it.
        print(f"{only.undecided} named no candidate — not scored")
    print()
    print(table(("technique", "attempts", "exact", "missed", "over"), rows(result)))

    # Printed in full, not summarised: reading them is how a mislabelled hand
    # claim is caught, and a corrected claim supersedes the earlier one.
    for disagreement in only.disagreements:
        user = " ".join(disagreement.user)
        machine = " ".join(disagreement.machine)
        print(f"\n{disagreement.attempt_id}\n  you: {user}\n  it:  {machine}")


def compared(result: Comparison) -> None:
    """Several configurations, every number over the attempts all of them read.

    What a column beside another buys is the denominator they share, without
    which two shares cannot be read against each other at all.
    """
    names = labels([scored.configuration for scored in result.scores])
    scores = [scored.score for scored in result.scores]

    print(f"{result.common} of {result.eval_set} hand-claimed attempts read by all")
    print()
    summary = [
        ("exact", [share(scored) for scored in scores]),
    ]
    if any(scored.decisions for scored in scores):
        summary.append(("per decision", [decided(scored) for scored in scores]))
    summary.append(("read/reused", [f"{scored.read}/{scored.reused}" for scored in scores]))
    if any(scored.undecided for scored in scores):
        summary.append(("named no candidate", [str(scored.undecided) for scored in scores]))
    print(table(("", *names), [(head, *cells) for head, cells in summary]))
    print()
    print(table(("technique", "attempts", *names), rows(result)))

    # Where they agreed there is nothing to choose between them, however wrong
    # both are — so only the splits are printed, and the code decides them.
    width = max(len(name) for name in names) + 1
    for split in result.splits:
        print(f"\n{split.attempt_id}\n  {'you:'.ljust(width)} {' '.join(split.user)}")
        for name, verdict in zip(names, split.verdicts, strict=True):
            print(f"  {(name + ':').ljust(width)} {' '.join(verdict)}")


def describe(configuration: Configuration) -> str:
    """Model and effort, and no rulebook: which criteria a reading was made
    against is a digest of what that attempt was sent, so it varies within one
    run and belongs on the record rather than in a heading."""
    return f"{configuration.model}, effort {configuration.effort}"


def labels(configurations: Sequence[Configuration]) -> list[str]:
    """A column heading per configuration: the model and the effort it ran at.

    Both always, though the model alone would name a column where no two share
    one. Effort moves a number as far as the model does, so a heading that
    dropped it would put two readings of the same model under one name and
    leave which is which to whoever remembers the command line.
    """
    return [f"{configuration.model}/{configuration.effort}" for configuration in configurations]


def exactly(scored: Score) -> str:
    return f"{scored.exact}/{scored.scored} exact ({scored.exact / scored.scored:.0%})"


def share(scored: Score) -> str:
    """The same number without the word, which the row label already carries."""
    return f"{scored.exact}/{scored.scored} ({scored.exact / scored.scored:.0%})"


def decided(scored: Score) -> str:
    """To a tenth, unlike the shares: the whole point of the row is that the
    configurations sit within a point or two of each other here while the
    shares spread out, and a rounded percent would hide the ordering."""
    return (
        f"{scored.decisions_agreed}/{scored.decisions} "
        f"({scored.decisions_agreed / scored.decisions:.1%})"
    )


def rows(result: Comparison) -> list[tuple[str, ...]]:
    """Per technique, since the board is — an overall number hides a code the
    classifier reaches for wrongly everywhere it is read.

    One `attempts` column however many configurations: the denominator is the
    hand claims, the same set for all of them. A technique no claim named is
    still a row, carrying the over-claims that put it there.
    """
    counted = [
        {row.technique: row for row in scored.score.per_technique} for scored in result.scores
    ]
    body = []
    for technique in sorted({name for rows in counted for name in rows}):
        found = [rows.get(technique) for rows in counted]
        attempts = max(row.attempts for row in found if row is not None)
        if len(found) == 1 and found[0] is not None:
            body.append((technique, str(attempts), *counts(found[0])))
        else:
            body.append((technique, str(attempts), *(packed(row) for row in found)))
    return body


def counts(row: TechniqueScore) -> tuple[str, str, str]:
    return str(row.exact), str(row.missed), str(row.over)


def packed(row: TechniqueScore | None) -> str:
    """One configuration's three counts in one column. A technique it never
    reached is three zeroes rather than a blank: it is a count, not a gap."""
    return "/".join(counts(row)) if row is not None else "0/0/0"


def announce(configuration: Configuration) -> None:
    """Which classifier the lines below came from. To stderr, beside the
    per-attempt progress it heads."""
    print(f"{describe(configuration)}:", file=sys.stderr, flush=True)


def table(header: Sequence[str], body: Sequence[Sequence[str]]) -> str:
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
