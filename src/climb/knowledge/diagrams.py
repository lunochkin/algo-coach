"""Mermaid sources drawn to SVG at the seed: `knowledge.md`, Diagrams."""

import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from sqlalchemy import Connection, select
from sqlalchemy.dialects.postgresql import insert

from climb.knowledge.files import ModuleSource
from climb.knowledge.table import diagrams
from climb.schema import Diagram

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


def fenced(text: str) -> list[str]:
    """A lesson's fenced sources, without the last newline a client drops."""
    return [m[1].rstrip("\n") for m in FENCE.finditer(text)]


def whole(diagram: object) -> str | None:
    """A question's diagram as a source, where one fence is all it holds."""
    m = WHOLE.match(diagram) if isinstance(diagram, str) else None
    return m[1].rstrip("\n") if m else None


def diagram_of(raw: dict[str, Any]) -> object:
    detail: object = raw.get("detail")
    return cast(dict[str, object], detail).get("diagram") if isinstance(detail, dict) else None


def mermaid_sources(module: ModuleSource) -> list[str]:
    """Every source the module's lessons and questions hold, each once."""
    found = [one for text in module.lesson_texts.values() for one in fenced(text)]
    found += [
        one for bank in module.banks for raw in bank.questions if (one := whole(diagram_of(raw)))
    ]
    return list(dict.fromkeys(found))


def drawings(conn: Connection, sources: list[str]) -> dict[str, dict[str, str]]:
    """Each drawn source's light and dark SVG, for the snapshot."""
    held = conn.execute(
        select(diagrams.c.source, diagrams.c.light, diagrams.c.dark).where(
            diagrams.c.source_hash.in_([source_hash(one) for one in sources])
        )
    )
    return {row.source: {"light": row.light, "dark": row.dark} for row in held}


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
