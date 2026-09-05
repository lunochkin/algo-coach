"""The bench a run was aimed with: which model writes what, from the flags.

`--site` opens a row and the settings after it fill it, as `--model` does in
`score`. A site nobody named keeps the built-in configuration, so a run naming
one site changes one call.
"""

import argparse
from collections.abc import Sequence

from algo_coach.cli.display import chosen
from algo_coach.generation import BENCH, Bench
from algo_coach.schema import Configuration

# Which slot each flag fills in the row a `--site` opens.
SLOTS = {"--model": 1, "--effort": 2, "--provider": 3, "--temperature": 4}

SITES = tuple(Bench.model_fields)


class Sited(argparse.Action):
    """`--site` and its settings alternately, into one ordered list. Separate
    `append` destinations would lose which model followed which site."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        rows: list[list[str]] = getattr(namespace, self.dest, None) or []
        if option_string == "--site":
            rows.append([str(value), "", "", "", ""])
        else:
            # never defaulted to a site: a model meant for one call would
            # otherwise land on whichever the list happens to open with
            if not rows:
                parser.exit(2, f"generate: name a --site before {option_string}\n")
            slot = SLOTS[str(option_string)]
            if rows[-1][slot]:
                parser.exit(2, f"generate: two {option_string} for one --site\n")
            rows[-1][slot] = str(value)
        setattr(namespace, self.dest, rows)


def bench(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Bench:
    """What the flags name, over the built-in bench."""
    rows = getattr(args, "sites", None)
    if not rows:
        return BENCH

    named: dict[str, Configuration] = {}
    for site, model, effort, provider, temperature in rows:
        if site not in SITES:
            parser.exit(2, f"generate: no call site {site!r}: {', '.join(SITES)}\n")
        if site in named:
            parser.exit(2, f"generate: two --site {site}\n")
        named[site] = configured(getattr(BENCH, site), parser, model, effort, provider, temperature)
    return BENCH.model_copy(update=named)


def configured(
    built_in: Configuration,
    parser: argparse.ArgumentParser,
    model: str,
    effort: str,
    provider: str,
    temperature: str,
) -> Configuration:
    # not defaulted to the built-in pin: an endpoint carries some models and
    # not others, so a model named without one would be routed anywhere
    if model and model != built_in.model and not provider:
        parser.exit(2, f"generate: --provider needed for {model}\n")
    return Configuration(
        model=model or built_in.model,
        effort=effort or built_in.effort,
        pin=provider or built_in.pin,
        temperature=chosen(temperature, parser, command="generate", fallback=built_in.temperature),
    )


__all__ = ["SITES", "SLOTS", "Sited", "bench", "configured"]
