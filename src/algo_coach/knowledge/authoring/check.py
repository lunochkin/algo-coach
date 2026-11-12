"""The module check: every rule `docs/authoring/rules.md` tags *check*, over
one module's files."""

import concurrent.futures as cf
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from algo_coach.knowledge.authoring.course import Report, load
from algo_coach.knowledge.authoring.execution import Runs
from algo_coach.knowledge.authoring.layout import box_drawing, text_fences, widths
from algo_coach.knowledge.authoring.lessons import lessons_run
from algo_coach.knowledge.authoring.likeness import overlaps
from algo_coach.knowledge.authoring.repeats import repeats
from algo_coach.knowledge.authoring.snippets import snippets, versions
from algo_coach.knowledge.authoring.static import (
    choices,
    coverage,
    kinds,
    lesson_links,
    library_versions,
    open_questions,
    positions,
    reused_ids,
)
from algo_coach.knowledge.authoring.tools import tool_outputs, transcripts

# kept beside the module, and gitignored by the content repository
CACHE = ".check-cache.json"
STATIC = (
    choices,
    kinds,
    positions,
    library_versions,
    open_questions,
    overlaps,
    repeats,
    lesson_links,
    text_fences,
    box_drawing,
    widths,
    coverage,
    reused_ids,
)


@dataclass
class Checked:
    report: Report
    # how many of each kind of run, in the order they ran
    ran: dict[str, int] = field(default_factory=dict[str, int])
    executed: int = 0


def check(
    root: Path, *, run: bool = True, other_versions: bool = True, fresh: bool = False
) -> Checked:
    course = load(root)
    kept = root / CACHE
    runs = Runs(json.loads(kept.read_text()) if kept.exists() and not fresh else None)
    checked = Checked(Report())
    report, ran = checked.report, checked.ran
    if run:
        with cf.ThreadPoolExecutor(os.cpu_count()) as pool:
            here = snippets(course, report, pool, runs)
            ran["snippets"] = len(here)
            ran["lesson blocks"] = lessons_run(course, report, pool, runs)
            ran["tool outputs"] = tool_outputs(course, report, pool, runs) + transcripts(
                course, report, runs
            )
            if other_versions:
                ran["runs on other interpreters"] = versions(course, report, pool, runs, here)
        kept.write_text(json.dumps(runs.cache))
    for rule in STATIC:
        rule(course, report)
    checked.executed = len(runs.executed)
    return checked
