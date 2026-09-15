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


def command() -> list[str]:
    # --pull never: a tag pulled per run would move under the run a verdict was
    # measured by
    return ["docker", "run", "--rm", "-i", "--pull", "never", IMAGE, "python", "-c", SCRIPT]


def docker(argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, input=stdin, capture_output=True, check=False)
