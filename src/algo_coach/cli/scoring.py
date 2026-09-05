"""What `score` prints: one configuration's numbers alone, or several side
by side, per technique and per attempt read differently."""

from collections.abc import Callable, Sequence

from algo_coach.claims import Comparison, ConfigurationScore, Score, TechniqueScore
from algo_coach.cli.display import UNSET, sampled
from algo_coach.schema import Configuration


# Which attempts a configuration failed on. With the numbers rather than as it
# happens: several answer at once, and a line in that stream names no row.
def failures(name: str, scored: Score) -> str:
    return "\n".join(
        [f"\n{name} failed on {len(scored.failed)}:"]
        + [f"  {one.attempt_id}  {one.reason}" for one in scored.failed]
    )


def columns(scores: Sequence[Score]) -> list[tuple[str, Callable[[Score], str]]]:
    """Which numbers a run reports, and how each renders. One list, shared by
    both renderers. A column is included only where some configuration has the
    number; `exact` is the ranking key and is printed apart."""
    shown: list[tuple[str, Callable[[Score], str]]] = []
    if any(scored.decisions for scored in scores):
        shown.append(("per decision", decided))
    shown.append(("read/reused", lambda scored: f"{scored.read}/{scored.reused}"))
    if any(scored.tokened for scored in scores):
        shown.append(("in/out/think", tokens))
    if any(scored.timed for scored in scores):
        shown.append(("mean/max", latency))
    if any(scored.costed for scored in scores):
        # A mean over the readings that carry a price, not over the eval set.
        shown.append(("per attempt", spent))
        shown.append(("set", outlay))
    if any(scored.undecided for scored in scores):
        shown.append(("named no candidate", considered))
    # Two columns: a cut-short reply names nothing for a reason unrelated to
    # the code.
    if any(scored.exhausted for scored in scores):
        shown.append(("cut short", lambda scored: str(scored.exhausted)))
    if any(scored.failed for scored in scores):
        shown.append(("failed", lambda scored: str(len(scored.failed))))
    return shown


def alone(result: Comparison) -> None:
    """One configuration: what it read, and every disagreement with the
    user."""
    only = result.scores[0].score
    print(describe(result.scores[0].configuration))
    print(exactly(only))
    # The comparison's columns, down the page rather than across it.
    named = [(name, cell(only)) for name, cell in columns([only])]
    width = max(len(name) for name, _ in named)
    for name, value in named:
        print(f"{name:<{width}}  {value}")
    if only.failed:
        print(failures(describe(result.scores[0].configuration), only))
    print()
    print(table(("technique", "attempts", "exact", "missed", "over"), rows(result.scores)))

    # In full: reading them is how a mislabelled hand claim is caught.
    for disagreement in only.disagreements:
        user = " ".join(disagreement.user)
        machine = " ".join(disagreement.machine)
        print(f"\n{disagreement.attempt_id}\n  you: {user}\n  it:  {machine}")


def compared(result: Comparison, *, splits: bool = False) -> None:
    """Several configurations, every number over the attempts all of them read.

    A row per configuration in the summary, a column per configuration in the
    per-technique table, keyed by number: a heading naming the whole
    configuration wrapped that table at six.
    """
    # Ranked here rather than in the domain, which keeps the command line's
    # order. A permutation rather than a sorted copy: a split's verdicts are
    # positional, so everything aligned with `Comparison.scores` follows it.
    order = sorted(
        range(len(result.scores)), key=lambda index: exact(result.scores[index].score), reverse=True
    )
    ranked = [result.scores[index] for index in order]
    scores = [scored.score for scored in ranked]
    keys = [str(index) for index in range(1, len(scores) + 1)]

    # Each share carries its own denominator; this line is how far they
    # overlap.
    print(f"{result.eval_set} hand-claimed attempts, {result.common} read by all")
    print()

    # The pin is here though `labels` drops it: a row has the width, and it is
    # the first thing to read when a configuration 404s.
    head = ["", "", "", "", "", "exact"]
    body = [
        [key, scored.configuration.model, scored.configuration.effort]
        + [sampled(scored.configuration.temperature), f"@ {scored.configuration.pin}"]
        + [share(scored.score)]
        for key, scored in zip(keys, ranked, strict=True)
    ]

    for name, cell in columns(scores):
        head.append(name)
        for row, scored in zip(body, scores, strict=True):
            row.append(cell(scored))
    print(table(head, body))

    # Behind the splits flag: a column per configuration, so forty is
    # unreadable.
    per_technique = rows(ranked)
    if splits:
        print()
        print(table(("technique", "attempts", *keys), per_technique))
    else:
        print(f"\n{len(per_technique)} techniques — --splits to see them per configuration")

    # Only the splits, and counted by default: one is a line per configuration.
    if result.splits and not splits:
        print(f"\n{len(result.splits)} read differently — --splits to see them")
    width = max(len("you"), *(len(key) for key in keys)) + 1
    for split in result.splits if splits else []:
        print(f"\n{split.attempt_id}\n  {'you:'.ljust(width)} {' '.join(split.user)}")
        for key, verdict in zip(keys, (split.verdicts[index] for index in order), strict=True):
            print(f"  {(key + ':').ljust(width)} {' '.join(verdict)}")

    # In full rather than by number: a failure block is often read alone.
    for key, scored in zip(keys, ranked, strict=True):
        if scored.score.failed:
            print(failures(f"{key}  {describe(scored.configuration)}", scored.score))


def describe(configuration: Configuration) -> str:
    """The whole configuration in a sentence, which `labels` says in a token.
    No rulebook: the criteria vary per attempt within one run."""
    temperature = UNSET if configuration.temperature is None else configuration.temperature
    return (
        f"{configuration.model}, effort {configuration.effort}, "
        f"temperature {temperature}, via {configuration.pin}"
    )


def labels(configurations: Sequence[Configuration]) -> list[str]:
    """Model, effort and temperature. Not the provider: it constrains who may
    answer rather than what was asked, so two columns cannot differ by it."""
    return [
        f"{configuration.model}/{configuration.effort}"
        f"@{UNSET if configuration.temperature is None else configuration.temperature}"
        for configuration in configurations
    ]


def exactly(scored: Score) -> str:
    return f"{scored.exact}/{scored.scored} exact ({scored.exact / scored.scored:.0%})"


# Unrounded: sorting on the printed percent ties configurations a point apart.
def exact(scored: Score) -> float:
    return scored.exact / scored.scored


def share(scored: Score) -> str:
    return f"{scored.exact}/{scored.scored} ({scored.exact / scored.scored:.0%})"


# To a tenth, unlike the shares: configurations sit a point or two apart here.
def decided(scored: Score) -> str:
    return (
        f"{scored.decisions_agreed}/{scored.decisions} "
        f"({scored.decisions_agreed / scored.decisions:.1%})"
    )


# What one attempt cost, over the readings that say. Six decimals: at four,
# everything below a tenth of a cent printed the same.
def spent(scored: Score) -> str:
    if not scored.costed:
        return "—"
    return f"${scored.cost / scored.costed:.6f}"


# Declines that judged the code, with the cut-short ones taken out.
def considered(scored: Score) -> str:
    return str(scored.undecided - scored.exhausted)


def tokens(scored: Score) -> str:
    """In, out and of that how much was thinking, per attempt. One column,
    since a verdict is a dozen tokens and everything above that is the model
    deciding."""
    if not scored.tokened:
        return "—"
    thinking = f"{round(scored.reasoning_tokens / scored.reasoned)}" if scored.reasoned else "—"
    return (
        f"{round(scored.input_tokens / scored.tokened)}/"
        f"{round(scored.output_tokens / scored.tokened)}/{thinking}"
    )


# Mean and worst: a mean alone cannot separate a reader that stalls on one
# attempt from a uniformly slow one.
def latency(scored: Score) -> str:
    if not scored.timed:
        return "—"
    return f"{scored.request_ms / scored.timed / 1000:.1f}/{scored.slowest_ms / 1000:.1f}s"


# What the whole set cost, where `spent` is the mean per attempt.
def outlay(scored: Score) -> str:
    return f"${scored.cost:.4f}" if scored.costed else "—"


def rows(scored_entries: Sequence[ConfigurationScore]) -> list[tuple[str, ...]]:
    """Per technique, as the board is. One `attempts` column however many
    configurations, since the denominator is the hand claims. A technique no
    claim named is still a row, carrying the over-claims that put it there."""
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


# A technique a configuration never reached is zeroes, not a blank: a count
# rather than a gap.
def packed(row: TechniqueScore | None) -> str:
    return "/".join(counts(row)) if row is not None else "0/0/0"


def table(header: Sequence[str], body: Sequence[Sequence[str]]) -> str:
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
