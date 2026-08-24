"""The transport the model-backed commands read models through.

One endpoint and one request shape: OpenRouter, spoken as chat completions.
Credentials come from the environment, so nothing about the account reaches
the store or this repo.
"""

import argparse
import os
import sys
from collections.abc import Callable

from openai import OpenAI

from algo_coach.calls import BASE_URL, OpenRouter, Retry
from algo_coach.cli.display import held

# What the transport resolves auth from. Checked before the run rather than
# left to the first request: an unset key fails every attempt in a backlog
# identically, and a per-attempt failure is reported per attempt.
CREDENTIALS = ("OPENROUTER_API_KEY",)


def warn(retry: Retry) -> None:
    """A cap, said as it is being waited out rather than inferred afterwards.

    One `write` of a complete line, because this is called on whichever thread
    made the request while other threads are printing progress. `print` builds
    its output in more than one write and the lines would interleave.

    To stderr, so a piped run keeps its report clean: a wait is something to
    watch, not part of what the command produced.
    """
    sys.stderr.write(held(retry) + "\n")


def transport(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    on_retry: Callable[[Retry], None] = warn,
) -> OpenRouter:
    key = next((os.environ[name] for name in CREDENTIALS if os.environ.get(name)), None)
    if key is None:
        parser.exit(2, f"{args.command}: {' or '.join(CREDENTIALS)} unset\n")
    # A line of its own by default. A command drawing a board takes the
    # report instead, since a warning written beside a block being redrawn
    # would scroll it.
    return OpenRouter(OpenAI(api_key=key, base_url=BASE_URL), on_retry=on_retry)
