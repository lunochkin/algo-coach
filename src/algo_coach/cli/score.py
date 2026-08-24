import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import (
    DEFAULT,
    Comparison,
    Configuration,
    ConfigurationScore,
    Score,
    TechniqueScore,
    score_backlog,
)
from algo_coach.claims.reading import Plan
from algo_coach.claims.run import ABORT_AFTER, Progress
from algo_coach.cli.display import UNSET, sampled
from algo_coach.cli.status import Status
from algo_coach.cli.transport import transport
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore

# `--temperature default` is how the provider's own is asked for: a named level
# rather than an omitted flag, as `--effort default` is. It is the arm every
# reading stored before the parameter existed sits in, so naming it is how
# those are scored beside a greedy run rather than discarded. Defined beside
# the formatting, since the board renders the same word.

# Which slot each flag fills in the row a `--model` opens. The order is the
# command line's, so the row is positional and the flags are not.
SLOTS = {"--effort": 1, "--provider": 2, "--temperature": 3}


class Named(argparse.Action):
    """`--model` and its settings alternately, into one ordered list.

    One action over every flag, because separate `append` destinations would
    lose which effort followed which model — and the command line's order is
    the output's. A model opens a configuration at the defaults; a setting
    fills the one just opened, or opens one at the default model coming first.
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
            named.append([str(value), "", "", ""])
        else:
            slot = SLOTS[str(option_string)]
            if not named:
                named.append([DEFAULT.model, "", "", ""])
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
    unpinned = [model for model, _, provider, _ in named if not provider and model != DEFAULT.model]
    if unpinned:
        # Not defaulted to the built-in pin: an endpoint carries some models and
        # not others, so inheriting one would route a model to a host that never
        # serves it. Not left to the router either — the readings would be a
        # mixture of builds under one key, which is what the pin exists to stop.
        parser.exit(2, f"score: --provider needed for {', '.join(sorted(set(unpinned)))}\n")
    built = tuple(
        Configuration(
            model=model,
            effort=effort or DEFAULT.effort,
            pin=provider or DEFAULT.pin,
            # Unlike the provider, part of what identifies a reading — so a
            # model named without one runs at the built-in temperature rather
            # than at whatever the endpoint defaults to. Two arms of one model
            # are told apart here and nowhere else.
            temperature=chosen(temperature, parser),
        )
        for model, effort, provider, temperature in named
    )
    if len(set(built)) != len(built):
        # Reading one configuration twice would measure its own sampling noise,
        # which nothing here consumes yet — refused rather than paid for.
        parser.exit(2, "score: the same configuration named twice\n")
    return built


def chosen(temperature: str, parser: argparse.ArgumentParser) -> float | None:
    """What a named model samples at: the built-in one where the flag was left
    off, and `None` only where it was asked for by name."""
    if not temperature:
        return DEFAULT.temperature
    if temperature == UNSET:
        return None
    try:
        return float(temperature)
    except ValueError:
        parser.exit(2, f"score: --temperature {temperature} is not a number or {UNSET!r}\n")
        raise


def score(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The classifier against the user's own claims. Every reading is stored,
    so a later run is paid for only where this one did not reach."""
    if args.stored and args.limit is not None:
        parser.exit(2, "score: --stored with --limit — a cap on a run that pays for nothing\n")
    named = configurations(args, parser)

    # Built before the transport, so a wait is reported onto the row it holds
    # rather than into the block being redrawn.
    board = Status(sys.stderr, named)
    # No credentials asked for by a run that makes no call: being runnable
    # anywhere is what makes the stored mode the reproducible one.
    api = None if args.stored else transport(args, parser, on_retry=board.waiting)
    log = AttemptLog(root)
    calls = CallLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}

    def planned(plans: Sequence[Plan]) -> None:
        board.planned([len(plan.asking) for plan in plans])

    def answered(configuration: Configuration, progress: Progress) -> None:
        board.answered(configuration, failed=progress.reason is not None)

    try:
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
            on_plan=planned,
            on_progress=answered,
        )
    finally:
        # In a `finally`, so a run that raised still leaves a whole block
        # rather than a half-drawn one.
        board.close()

    if not result.eval_set:
        parser.exit(1, f"score: nothing hand-claimed to score against for {args.user}\n")
    aborted = [
        name
        for name, scored in zip(labels(named), result.scores, strict=True)
        if scored.score.aborted
    ]
    if aborted:
        # The numbers are withheld, the reasons are not. What a configuration
        # read before it broke is a slice of the eval set, and a share over it
        # would be read as its answer — but a run that ends here is one nothing
        # else will explain, since the board carries a tally and no tally names
        # an attempt.
        for name, scored in zip(labels(named), result.scores, strict=True):
            if scored.score.failed:
                print(failures(name, scored.score), file=sys.stderr)
        parser.exit(
            1,
            f"\nscore: {', '.join(aborted)} aborted after {ABORT_AFTER} consecutive failures\n",
        )
    if not result.common:
        # Told apart from the above: ground truth exists and no reading of it
        # does — a stored run before anything was read, or every call failing.
        parser.exit(1, "score: nothing every configuration named has read\n")

    if len(result.scores) == 1:
        alone(result)
    else:
        compared(result, splits=args.splits)


def failures(name: str, scored: Score) -> str:
    """Which attempts a configuration failed on, and why.

    The board carries a tally per row, and a tally names no attempt. Printed
    with the numbers rather than as it happens: several configurations answer
    at once, and a line in that stream cannot say which produced it.
    """
    return "\n".join(
        [f"\n{name} failed on {len(scored.failed)}:"]
        + [f"  {one.attempt_id}  {one.reason}" for one in scored.failed]
    )


def alone(result: Comparison) -> None:
    """One configuration: what it read, and every disagreement with the user."""
    only = result.scores[0].score
    print(describe(result.scores[0].configuration))
    print(exactly(only))
    if only.decisions:
        print(decided(only))
    print(f"{only.read} read, {only.reused} reused")
    if only.tokened:
        print(f"{tokens(only)} tokens in/out/thinking per attempt")
    if only.timed:
        print(f"{latency(only)} per request, mean and slowest")
    if only.costed:
        print(f"{spent(only)} per attempt, {outlay(only)} over {only.costed} priced reading(s)")
    if only.undecided:
        # Beside the share, since declining shrinks the denominator and
        # improves the number for it.
        print(f"{only.undecided} named no candidate — not scored")
    if only.failed:
        print(failures(describe(result.scores[0].configuration), only))
    print()
    print(table(("technique", "attempts", "exact", "missed", "over"), rows(result.scores)))

    # Printed in full, not summarised: reading them is how a mislabelled hand
    # claim is caught, and a corrected claim supersedes the earlier one.
    for disagreement in only.disagreements:
        user = " ".join(disagreement.user)
        machine = " ".join(disagreement.machine)
        print(f"\n{disagreement.attempt_id}\n  you: {user}\n  it:  {machine}")


def compared(result: Comparison, *, splits: bool = False) -> None:
    """Several configurations, every number over the attempts all of them read.

    What a column beside another buys is the denominator they share, without
    which two shares cannot be read against each other at all.

    The summary is a row per configuration and the per-technique table a column
    per configuration, because only one of them can grow sideways. Techniques
    are what the second table compares along, so the configurations there are
    a number, and the summary is where that number is spelled out. A heading
    naming the whole configuration wrapped the table at six of them, and a
    wrapped table compares nothing.

    Only the summary is printed by default. The per-technique table still grows
    a column per configuration, which a number rather than a name only delays —
    at forty it wraps whatever the heading says.
    """
    # Ranked here rather than in the domain, which keeps the command line's
    # order so a caller can zip its own configurations against the readings.
    # What a comparison is read for is which classifier won, and finding that
    # down a column of fifty shares is work the sort does once. Ties keep the
    # order they were named in, since the sort is stable.
    #
    # A permutation rather than a sorted copy. Everything else aligned with
    # `Comparison.scores` has to follow, and a split's verdicts are positional.
    # Reordering the rows alone would file each verdict under the wrong
    # configuration.
    order = sorted(
        range(len(result.scores)), key=lambda index: exact(result.scores[index].score), reverse=True
    )
    ranked = [result.scores[index] for index in order]
    scores = [scored.score for scored in ranked]
    keys = [str(index) for index in range(1, len(scores) + 1)]

    print(f"{result.common} of {result.eval_set} hand-claimed attempts read by all")
    print()

    # No heading over the identity columns: the row says what it is, and a
    # word above it would only repeat the configuration underneath. The pin is
    # among them here though `labels` drops it — a row has the width a heading
    # did not, and it is the first thing to read when a configuration 404s.
    head = ["", "", "", "", "", "exact"]
    body = [
        [key, scored.configuration.model, scored.configuration.effort]
        + [sampled(scored.configuration.temperature), f"@ {scored.configuration.pin}"]
        + [share(scored.score)]
        for key, scored in zip(keys, ranked, strict=True)
    ]

    def column(name: str, cell: Callable[[Score], str]) -> None:
        head.append(name)
        for row, scored in zip(body, scores, strict=True):
            row.append(cell(scored))

    if any(scored.decisions for scored in scores):
        column("per decision", decided)
    column("read/reused", lambda scored: f"{scored.read}/{scored.reused}")
    if any(scored.tokened for scored in scores):
        column("in/out/think", tokens)
    if any(scored.timed for scored in scores):
        column("mean/max", latency)
    if any(scored.costed for scored in scores):
        # A mean over the readings that carry a price, not over the eval set:
        # one stored before the router's charge was recorded says nothing, and
        # counting it as free would flatter whichever configuration was read
        # earliest.
        column("per attempt", spent)
        column("set", outlay)
    if any(scored.undecided for scored in scores):
        column("named no candidate", lambda scored: str(scored.undecided))
    if any(scored.failed for scored in scores):
        # Beside `read/reused`, which is where a shrunken denominator is
        # diagnosed: a configuration that failed read fewer than it planned to.
        column("failed", lambda scored: str(len(scored.failed)))
    print(table(head, body))

    # Behind the same flag as the splits, and for the same reason: a column per
    # configuration, so forty of them is a table nothing can read. The summary
    # answers which classifier won, which is what a wide run is for. Where one
    # of them goes wrong is a question asked of a shortlist.
    per_technique = rows(ranked)
    if splits:
        print()
        print(table(("technique", "attempts", *keys), per_technique))
    else:
        print(f"\n{len(per_technique)} techniques — --splits to see them per configuration")

    # Where they agreed there is nothing to choose between them, however wrong
    # both are — so only the splits are ever printed, and the code decides them.
    # Counted rather than printed by default: one split is a line per
    # configuration, so ten of them turn a handful of disagreements into
    # hundreds of lines that mostly repeat each other.
    if result.splits and not splits:
        print(f"\n{len(result.splits)} read differently — --splits to see them")
    width = max(len("you"), *(len(key) for key in keys)) + 1
    for split in result.splits if splits else []:
        print(f"\n{split.attempt_id}\n  {'you:'.ljust(width)} {' '.join(split.user)}")
        for key, verdict in zip(keys, (split.verdicts[index] for index in order), strict=True):
            print(f"  {(key + ':').ljust(width)} {' '.join(verdict)}")

    # Named in full here rather than by number: a failure block is read on its
    # own, often pasted somewhere the summary above it did not go.
    for key, scored in zip(keys, ranked, strict=True):
        if scored.score.failed:
            print(failures(f"{key}  {describe(scored.configuration)}", scored.score))


def describe(configuration: Configuration) -> str:
    """The whole configuration in a sentence, which the column heading says in
    a token. Two arms of one model can differ by the temperature alone. A
    heading naming only the model and the effort would announce them
    identically, leaving which is running to whoever remembers the command
    line.

    The pin is here and not in the heading: it identifies a reading like the
    rest, but a column is already unambiguous without it, and it is the first
    thing to read when one of them 404s.

    No rulebook, at either place. Which criteria a reading was made against is
    a digest of what that attempt was sent, so it varies within one run and
    belongs on the record."""
    temperature = UNSET if configuration.temperature is None else configuration.temperature
    return (
        f"{configuration.model}, effort {configuration.effort}, "
        f"temperature {temperature}, via {configuration.pin}"
    )


def labels(configurations: Sequence[Configuration]) -> list[str]:
    """A short name per configuration: the model and the effort it ran at.

    All three always, though the model alone would name a column where no two
    share one. Effort and temperature each move a number as far as the model
    does. A heading that dropped one would put two readings of the same model
    under one name, leaving which is which to whoever remembers the command
    line. The provider is not among them. It constrains who may answer rather
    than what was asked, so two columns can never differ by it alone.
    """
    return [
        f"{configuration.model}/{configuration.effort}"
        f"@{UNSET if configuration.temperature is None else configuration.temperature}"
        for configuration in configurations
    ]


def exactly(scored: Score) -> str:
    return f"{scored.exact}/{scored.scored} exact ({scored.exact / scored.scored:.0%})"


def exact(scored: Score) -> float:
    """The share as a number. What the table prints is rounded to a percent,
    and sorting on that would call two configurations a point apart equal."""
    return scored.exact / scored.scored


def share(scored: Score) -> str:
    """The same number without the word, which the row label already carries."""
    return f"{scored.exact}/{scored.scored} ({scored.exact / scored.scored:.0%})"


def decided(scored: Score) -> str:
    """To a tenth, unlike the shares. The point of the row is that the
    configurations sit within a point or two of each other here while the
    shares spread out, and a rounded percent would hide the ordering."""
    return (
        f"{scored.decisions_agreed}/{scored.decisions} "
        f"({scored.decisions_agreed / scored.decisions:.1%})"
    )


def spent(scored: Score) -> str:
    """What one attempt cost this configuration, averaged over the readings
    that say. Six decimals, since the cheapest column reads a whole eval set
    for well under a cent — at four, everything below a tenth of a cent printed
    as the same number."""
    if not scored.costed:
        return "—"
    return f"${scored.cost / scored.costed:.6f}"


def tokens(scored: Score) -> str:
    """In, out and of that how much was thinking, per attempt.

    Three numbers rather than three columns: they are read against each other,
    since a verdict is a dozen tokens and everything above that is the model
    deciding. A dash for the split where the router reported none.
    """
    if not scored.tokened:
        return "—"
    thinking = f"{round(scored.reasoning_tokens / scored.reasoned)}" if scored.reasoned else "—"
    return (
        f"{round(scored.input_tokens / scored.tokened)}/"
        f"{round(scored.output_tokens / scored.tokened)}/{thinking}"
    )


def latency(scored: Score) -> str:
    """How long the answering request took, on average and at its worst.

    Seconds, since these run in tens of them and milliseconds would be five
    digits of false precision. The worst is worth its own number: a reader that
    stalls on one attempt in eighty is a different problem from one that is
    uniformly slow, and a mean cannot tell them apart.
    """
    if not scored.timed:
        return "—"
    return f"{scored.request_ms / scored.timed / 1000:.1f}/{scored.slowest_ms / 1000:.1f}s"


def outlay(scored: Score) -> str:
    """What the whole set cost, which is the figure a run is decided on. The
    mean says which classifier is dear; this says whether the comparison was
    worth running."""
    return f"${scored.cost:.4f}" if scored.costed else "—"


def rows(scored_entries: Sequence[ConfigurationScore]) -> list[tuple[str, ...]]:
    """Per technique, since the board is — an overall number hides a code the
    classifier reaches for wrongly everywhere it is read.

    One `attempts` column however many configurations: the denominator is the
    hand claims, the same set for all of them. A technique no claim named is
    still a row, carrying the over-claims that put it there.
    """
    counted = [
        {row.technique: row for row in scored.score.per_technique} for scored in scored_entries
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


def table(header: Sequence[str], body: Sequence[Sequence[str]]) -> str:
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
