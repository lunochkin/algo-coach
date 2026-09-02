import argparse
import os
import sys
from collections.abc import Callable

from openai import OpenAI

from algo_coach.calls import BASE_URL, OpenRouter, Retry
from algo_coach.cli.display import held

# Checked before the run: an unset key fails a whole backlog identically.
CREDENTIALS = ("OPENROUTER_API_KEY",)


def warn(retry: Retry) -> None:
    # One `write` of a whole line: this runs on the requesting thread while
    # others print, and `print` emits in several writes.
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
    # A command drawing a board passes its own `on_retry`, or the line scrolls
    # the block.
    return OpenRouter(OpenAI(api_key=key, base_url=BASE_URL), on_retry=on_retry)
