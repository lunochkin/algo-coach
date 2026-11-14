"""learn's history, read from its data repo and posted through the sync the
app uses. A `client_id` names each line's place, so a second import stores
nothing again."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from climb.knowledge.sync import KINDS as KINDS_STORED
from climb.knowledge.sync import Refusal, sync
from climb.storage import Database

# learn's folder per kind of record, against the sync's line kinds; attempts
# sit in the device's own folder
KINDS = {
    "": "attempt",
    "sessions": "session",
    "status": "status",
    "focus": "focus",
    "lessons": "lesson",
    "certs": "cert",
}
# past every append order a table holds, so the sync reads nothing back
NOTHING_BACK = 2**62


class ImportReport(BaseModel):
    read: int = 0
    stored: int = 0
    known: int = 0  # imported before, under the same `client_id`
    refused: list[Refusal] = []


def learn_lines(base: Path) -> dict[str, list[dict[str, Any]]]:
    """Every line of `progress/<device>/`, by device, named by its place."""
    devices: dict[str, list[dict[str, Any]]] = {}
    for path in sorted((base / "progress").glob("*/**/*.jsonl")):
        place = path.relative_to(base / "progress")
        device, folders = place.parts[0], place.parts[1:-1]
        kind = KINDS.get(folders[0] if folders else "")
        if kind is None:
            continue
        for number, text in enumerate(path.read_text().splitlines()):
            if text.strip():
                line = json.loads(text) | {"kind": kind, "client_id": f"learn:{place}:{number}"}
                devices.setdefault(device, []).append(line)
    return devices


def imported(root: Database, user_id: str, base: Path) -> ImportReport:
    report = ImportReport()
    for device, lines in learn_lines(base).items():
        since = {table.name: NOTHING_BACK for table, _ in KINDS_STORED.values()}
        result = sync(root, user_id, device, lines, since)
        report.read += len(lines)
        report.stored += result.stored
        report.known += result.known
        report.refused += result.refused
    return report
