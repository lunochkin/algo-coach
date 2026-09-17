"""A run's container: one `docker run -i`, the entry process's script as its
command and the run on its standard input."""

import contextlib
import os
import selectors
import subprocess
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Literal

# the submission's image: an interpreter and no engine code. By digest, since a
# tag moves under the run a stored verdict was measured by. The index's digest,
# so each host resolves its own platform from it; the tag is only for a reader
DIGEST = "sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6"
IMAGE = f"python:3.14-slim@{DIGEST}"

# read as a file rather than imported: importing it would load the runner's
# package, and the process holding the socket loads no engine code
SCRIPT = (Path(__file__).parent.parent / "runner" / "child.py").read_text()

# every run's container carries it, so a starting broker finds the containers
# a broker that died mid-run left
LABEL = "algo-coach.run"

# gVisor, named here and never by a request: `docs/architecture/README.md`
RUNTIME = "runsc"
# nobody, by number, so the image's own user list decides nothing
USER = "65534:65534"
# the whole container: the entry process, a case's child and gVisor's own share.
# Swap equal to it, so a run past the limit is refused rather than paged out
MEMORY = "512m"
# every process of the container, gVisor's own among them, since gVisor backs
# each process a case starts with a host process. A backstop above the limit
# `child.py` sets on each case, because reaching this one ends the sandbox
PROCESSES = "256"
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
    # an init as the container's first process, which reaps what a solution
    # orphaned. A zombie counts against the process limit, and the entry
    # process reaps only the children it forked itself
    "--init",
    # tells the entry process that its user owns this run alone, so the process
    # limit it sets on each case counts the run's processes and nothing else
    "--env",
    "ALGO_COACH_SANDBOX=1",
)

# a case's result line: a value within the 1 MiB ceiling, encoded once more
# inside the line, and a traceback beside it
OUTPUT_PER_CASE = 4 << 20
# docker's own messages, and the entry process's traceback on a fault
OUTPUT_SLACK = 64 << 10

# above the entry process's own slack of 2 s a case, so a sound entry's timer
# fires first
CASE_SLACK_MS = 3000
# the container's start under gVisor and the interpreter's, which no cap counts
STARTUP_MS = 10_000
# one docker command of the broker's own, which a daemon under load answers
# slowly
DOCKER_SECONDS = 10
# the image's first pull, over the host's own connection
PULL_SECONDS = 300


@dataclass(frozen=True)
class Finished:
    """How a command ended, and what it wrote until then."""

    how: Literal["exited", "overflowed", "expired"]
    returncode: int
    stdout: bytes
    stderr: bytes


type Execute = Callable[[list[str], bytes, int, float], Finished]
type Stop = Callable[[str], None]
type Clear = Callable[[], None]
type Pull = Callable[[], None]


def output_limit(cases: int) -> int:
    return cases * OUTPUT_PER_CASE + OUTPUT_SLACK


def deadline(cases: int, cap_ms: int) -> float:
    """The seconds a run may take: every case's cap and slack, and the start."""
    return (cases * (cap_ms + CASE_SLACK_MS) + STARTUP_MS) / 1000


def container_name() -> str:
    return f"algo-coach-run-{uuid.uuid4().hex}"


def command(name: str) -> list[str]:
    # --pull never: the broker pulled the pinned image when it started, and a
    # run never waits on a registry. --name: the client dying leaves the
    # container running, so past the deadline the container is killed by name
    return [
        "docker",
        "run",
        "--rm",
        "-i",
        "--pull",
        "never",
        "--name",
        name,
        "--label",
        LABEL,
        *FLAGS,
        IMAGE,
        "python",
        "-c",
        SCRIPT,
    ]


def docker(argv: list[str], stdin: bytes, limit: int, seconds: float) -> Finished:
    """The command, its output read to `limit` bytes across both streams and
    its run to `seconds`, and the command killed past either."""
    process = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    # beside the read rather than before it, so a command that never reads its
    # input cannot hold the broker past the deadline
    threading.Thread(target=_feed, args=(process.stdin, stdin), daemon=True).start()
    try:
        how, stdout, stderr = _bounded(
            process.stdout.fileno(), process.stderr.fileno(), limit, time.monotonic() + seconds
        )
        if how != "exited":
            # the client alone: the container outlives it, and the route stops
            # the container by name
            process.kill()
        if how == "overflowed":
            stdout, stderr = b"", f"the run's output passed {limit} bytes".encode()
        return Finished(how, process.wait(), stdout, stderr)
    finally:
        process.stdout.close()
        process.stderr.close()


def kill(name: str) -> None:
    """Stops a run's container. One already gone answers that no such container
    exists, which is the same end."""
    with contextlib.suppress(subprocess.TimeoutExpired):
        subprocess.run(
            ["docker", "kill", name], capture_output=True, check=False, timeout=DOCKER_SECONDS
        )


def remove_leftovers(label: str = LABEL) -> None:
    """Removes every container carrying `label`, running or not."""
    # a failed listing is raised: a broker that cannot reach docker has no run
    # to answer, so it does not start
    listed = subprocess.run(
        ["docker", "ps", "--all", "--quiet", "--filter", f"label={label}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=DOCKER_SECONDS,
    )
    if ids := listed.stdout.split():
        # unchecked: a container `--rm` removed since the listing is the same
        # end
        subprocess.run(
            ["docker", "rm", "--force", *ids],
            capture_output=True,
            check=False,
            timeout=DOCKER_SECONDS,
        )


def pull_image() -> None:
    # the host's daemon pulls, since the broker's own network leads nowhere
    subprocess.run(["docker", "pull", IMAGE], capture_output=True, check=True, timeout=PULL_SECONDS)


def _feed(pipe: IO[bytes], data: bytes) -> None:
    view = memoryview(data)
    # a command that exited, or was killed, closed the pipe
    with contextlib.suppress(OSError):
        while view:
            view = view[pipe.write(view) :]
    with contextlib.suppress(OSError):
        pipe.close()


def _bounded(
    out: int, err: int, limit: int, until: float
) -> tuple[Literal["exited", "overflowed", "expired"], bytes, bytes]:
    """Both streams to their end, or to the point they carry more than `limit`
    bytes together, or to `until`, whichever comes first."""
    # both at once: a stream left unread fills its pipe and stalls the other
    kept = {out: bytearray(), err: bytearray()}
    total = 0
    with selectors.DefaultSelector() as selector:
        for fd in kept:
            selector.register(fd, selectors.EVENT_READ)
        while selector.get_map():
            left = until - time.monotonic()
            if left <= 0:
                return "expired", bytes(kept[out]), bytes(kept[err])
            for key, _ in selector.select(left):
                chunk = os.read(key.fd, 1 << 16)
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                total += len(chunk)
                if total > limit:
                    return "overflowed", b"", b""
                kept[key.fd] += chunk
    return "exited", bytes(kept[out]), bytes(kept[err])
