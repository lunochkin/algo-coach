"""Mermaid sources drawn to SVG at the seed: `knowledge.md`, Diagrams."""

import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from sqlalchemy import Connection, select
from sqlalchemy.dialects.postgresql import insert

from algo_coach.knowledge.files import ModuleSource
from algo_coach.knowledge.table import diagrams
from algo_coach.schema import Diagram

FENCE = re.compile(r"^```mermaid\n(.*?)^```", re.S | re.M)
# a question's diagram is Mermaid where its whole text is one fence
WHOLE = re.compile(r"\A\s*```mermaid\n(.*?)^```\s*\Z", re.S | re.M)
TOOL = Path(__file__).resolve().parents[3] / "tools" / "diagrams"


class DrawError(Exception):
    pass


class Drawer(Protocol):
    def version(self) -> str: ...

    def draw(self, sources: list[str]) -> list[tuple[str, str]]:
        """Each source's light and dark SVG, in order."""
        ...


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def mermaid_sources(module: ModuleSource) -> list[str]:
    """Every source a lesson fences or a question's diagram holds, each once,
    without the newline ending its last line: a client's parser drops it."""
    found = [m[1] for text in module.lesson_texts.values() for m in FENCE.finditer(text)]
    for bank in module.banks:
        for raw in bank.questions:
            detail: object = raw.get("detail")
            diagram: object = (
                cast(dict[str, object], detail).get("diagram") if isinstance(detail, dict) else None
            )
            if isinstance(diagram, str) and (m := WHOLE.match(diagram)):
                found.append(m[1])
    return list(dict.fromkeys(one.rstrip("\n") for one in found))


class MermaidCli:
    """The drawing tool in `tools/diagrams`, run under Node on the author's
    machine."""

    def _run(self, args: list[str], stdin: str = "") -> str:
        if not (TOOL / "node_modules").is_dir():
            raise DrawError("the drawing tool is not installed: run `just diagrams-install`")
        ran = subprocess.run(
            ["node", "draw.mjs", *args], cwd=TOOL, input=stdin, capture_output=True, text=True
        )
        if ran.returncode:
            raise DrawError(ran.stderr.strip())
        return ran.stdout

    def version(self) -> str:
        return self._run(["--version"]).strip()

    def draw(self, sources: list[str]) -> list[tuple[str, str]]:
        out = json.loads(self._run([], json.dumps(sources)))
        return [(one["light"], one["dark"]) for one in out["drawings"]]


def undrawn(conn: Connection, sources: list[str], tool: str) -> list[str]:
    """The sources with no drawing by this version of the tool."""
    held = conn.execute(
        select(diagrams.c.source_hash).where(
            diagrams.c.source_hash.in_([source_hash(one) for one in sources]),
            diagrams.c.tool == tool,
        )
    ).scalars()
    done = set(held)
    return [one for one in sources if source_hash(one) not in done]


def store(conn: Connection, sources: list[str], drawn: list[tuple[str, str]], tool: str) -> None:
    now = datetime.now(UTC)
    for source, (light, dark) in zip(sources, drawn, strict=True):
        row = Diagram(
            source_hash=source_hash(source),
            source=source,
            tool=tool,
            light=light,
            dark=dark,
            drawn_at=now,
        ).model_dump()
        upsert = insert(diagrams).values(row)
        conn.execute(
            upsert.on_conflict_do_update(
                index_elements=[diagrams.c.source_hash],
                set_={k: upsert.excluded[k] for k in ("tool", "light", "dark", "drawn_at")},
            )
        )
