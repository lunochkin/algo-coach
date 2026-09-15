"""A run's container: one `docker run -i`, the entry process's script as its
command and the run on its standard input."""

import subprocess
from collections.abc import Callable
from pathlib import Path

# the submission's image: an interpreter and no engine code
IMAGE = "python:3.14-slim"

# read as a file rather than imported: importing it would load the runner's
# package, and the process holding the socket loads no engine code
SCRIPT = (Path(__file__).parent.parent / "runner" / "child.py").read_text()

type Execute = Callable[[list[str], bytes], subprocess.CompletedProcess[bytes]]

# gVisor, named here and never by a request: `docs/architecture/README.md`
RUNTIME = "runsc"
# nobody, by number, so the image's own user list decides nothing
USER = "65534:65534"
# docker's options, so they sit before the image: after it they would be
# arguments to `python`
FLAGS = (
    "--runtime",
    RUNTIME,
    "--network",
    "none",
    "--read-only",
    "--user",
    USER,
    "--cap-drop",
    "ALL",
    "--security-opt",
    "no-new-privileges",
)


def command() -> list[str]:
    # --pull never: a tag pulled per run would move under the run a verdict was
    # measured by
    return [
        "docker",
        "run",
        "--rm",
        "-i",
        "--pull",
        "never",
        *FLAGS,
        IMAGE,
        "python",
        "-c",
        SCRIPT,
    ]


def docker(argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, input=stdin, capture_output=True, check=False)
