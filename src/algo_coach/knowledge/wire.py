"""learn's log lines, the shape the app writes and reads, mapped to this
project's records and back. Content is named by slug on the wire and by id in
the store."""

from typing import Any

LEVELS = ("foundation", "associate", "professional", "expert")
# a certification whose scope is the whole module, in learn's id
WHOLE = "all"
# learn's queue modes against this project's: `knowledge.md`, Queues
LEARN_MODES = {"drill": "filtered"}
OUR_MODES = {ours: theirs for theirs, ours in LEARN_MODES.items()}
EXAM = "exam-L"


class Unknown(Exception):
    """A record naming content the store does not hold. The client drops it."""


def mode_in(mode: str) -> tuple[str, int | None]:
    if mode.startswith(EXAM):
        return "exam", int(mode.removeprefix(EXAM))
    return LEARN_MODES.get(mode, mode), None


def mode_out(mode: str, rank: int | None) -> str:
    return f"{EXAM}{rank}" if mode == "exam" else OUR_MODES.get(mode, mode)


def certification_in(module: str, certification: str) -> tuple[str | None, int]:
    """learn's `<module>-<scope>-<rank name>`, as a topic slug or none for the
    whole module, and a rank."""
    scope, _, rank = certification.removeprefix(f"{module}-").rpartition("-")
    if rank not in LEVELS or not scope:
        raise Unknown(f"unknown certification {certification}")
    return (None if scope == WHOLE else scope), LEVELS.index(rank)


def certification_out(module: str, topic: str | None, rank: int) -> str:
    return f"{module}-{topic or WHOLE}-{LEVELS[rank]}"


def answer_out(row: dict[str, Any]) -> dict[str, Any]:
    """learn's attempt line, leaving out what learn left out when empty."""
    line: dict[str, Any] = {"course": row["module"], "id": row["question"], "ok": row["correct"]}
    if row["guess"]:
        line["guess"] = True
    if row["grade"] is not None:
        line["grade"] = row["grade"]
    for ticks in ("missed", "traps"):
        if row[ticks]:
            line[ticks] = row[ticks]
    if row["wrong"]:
        line["wrong"] = True
    return line
