"""The transport the model-backed commands read models through.

One endpoint and one request shape: OpenRouter, spoken as chat completions.
Credentials come from the environment, so nothing about the account reaches
the store or this repo.
"""

import argparse
import os

from openai import OpenAI

from algo_coach.calls import BASE_URL, OpenRouter

# What the transport resolves auth from. Checked before the run rather than
# left to the first request: an unset key fails every attempt in a backlog
# identically, and a per-attempt failure is reported per attempt.
CREDENTIALS = ("OPENROUTER_API_KEY",)


def transport(args: argparse.Namespace, parser: argparse.ArgumentParser) -> OpenRouter:
    key = next((os.environ[name] for name in CREDENTIALS if os.environ.get(name)), None)
    if key is None:
        parser.exit(2, f"{args.command}: {' or '.join(CREDENTIALS)} unset\n")
    return OpenRouter(OpenAI(api_key=key, base_url=BASE_URL))
