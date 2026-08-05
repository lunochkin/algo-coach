"""The client the model-backed commands read the API through.

Credentials come from the environment, so nothing about the account reaches the
store or this repo.
"""

import argparse
import os

from anthropic import Anthropic

# What the SDK resolves auth from. Checked before the run rather than left to
# the first request: an unset key fails every attempt in a backlog identically,
# and a per-attempt failure is reported per attempt.
CREDENTIALS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def client(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Anthropic:
    if not any(os.environ.get(name) for name in CREDENTIALS):
        parser.exit(2, f"{args.command}: {' or '.join(CREDENTIALS)} unset\n")
    return Anthropic()
