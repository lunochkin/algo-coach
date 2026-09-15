"""A run's container: one `docker run -i`, the entry process's script as its
command and the run on its standard input."""

import contextlib
import os
import selectors
import subprocess
from collections.abc import Callable
from pathlib import Path

# the submission's image: an interpreter and no engine code
IMAGE = "python:3.14-slim"

# read as a file rather than imported: importing it would load the runner's
# package, and the process holding the socket loads no engine code
SCRIPT = (Path(__file__).parent.parent / "runner" / "child.py").read_text()

type Execute = Callable[[list[str], bytes, int], subprocess.CompletedProcess[bytes]]

# gVisor, named here and never by a request: `docs/architecture/README.md`
RUNTIME = "runsc"
# nobody, by number, so the image's own user list decides nothing
USER = "65534:65534"
# the whole container: the entry process, a case's child and gVisor's own share.
# Swap equal to it, so a run past the limit is refused rather than paged out
MEMORY = "512m"
# the entry process, a case's child, and whatever the solution starts
PROCESSES = "64"
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
    "--memory",
    MEMORY,
    "--memory-swap",
    MEMORY,
    "--pids-limit",
    PROCESSES,
)

# a case's result line: a value within the 1 MiB ceiling, encoded once more
# inside the line, and a traceback beside it
OUTPUT_PER_CASE = 4 << 20
# docker's own messages, and the entry process's traceback on a fault
OUTPUT_SLACK = 64 << 10


def output_limit(cases: int) -> int:
    return cases * OUTPUT_PER_CASE + OUTPUT_SLACK


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


def docker(argv: list[str], stdin: bytes, limit: int) -> subprocess.CompletedProcess[bytes]:
    """The command's output, read to `limit` bytes across both streams, and the
    command killed past it."""
    process = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    # whole before reading: the entry process reads the run to its end before
    # it prints. A command that exited early closed the pipe
    view = memoryview(stdin)
    with contextlib.suppress(BrokenPipeError):
        while view:
            view = view[process.stdin.write(view) :]
    process.stdin.close()
    try:
        read = _bounded([process.stdout.fileno(), process.stderr.fileno()], limit)
        if read is None:
            # the client, not the container: killing a run's container by name
            # is the outer timer's step
            process.kill()
            message = f"the run's output passed {limit} bytes".encode()
            return subprocess.CompletedProcess(argv, process.wait(), b"", message)
        stdout, stderr = read
        return subprocess.CompletedProcess(argv, process.wait(), stdout, stderr)
    finally:
        process.stdout.close()
        process.stderr.close()


def _bounded(fds: list[int], limit: int) -> list[bytes] | None:
    """Each stream to its end, or `None` once they carry more than `limit`
    bytes together."""
    # both at once: a stream left unread fills its pipe and stalls the other
    kept = {fd: bytearray() for fd in fds}
    total = 0
    with selectors.DefaultSelector() as selector:
        for fd in fds:
            selector.register(fd, selectors.EVENT_READ)
        while selector.get_map():
            for key, _ in selector.select():
                chunk = os.read(key.fd, 1 << 16)
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                total += len(chunk)
                if total > limit:
                    return None
                kept[key.fd] += chunk
    return [bytes(kept[fd]) for fd in fds]
