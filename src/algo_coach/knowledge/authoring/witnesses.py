"""Rule 26: a concept's witness prints its recorded output on the project's
interpreter and on every version and build check.toml names."""

import concurrent.futures as cf
import sys

from algo_coach.knowledge.authoring.course import Course, Report
from algo_coach.knowledge.authoring.execution import Ran, Runs
from algo_coach.knowledge.authoring.snippets import find


def witnesses(
    course: Course, report: Report, pool: cf.Executor, runs: Runs, other_versions: bool
) -> int:
    pythons = {"the project's interpreter": sys.executable}
    if other_versions:
        specs = course.versions + course.builds
        pythons |= {spec: python for spec in specs if (python := find(spec, report))}
    jobs: dict[cf.Future[Ran], tuple[str, str]] = {
        pool.submit(runs.run, concept["witness"].lstrip("\n"), python): (name, spec)
        for name, concept in course.concepts.items()
        if "witness" in concept
        for spec, python in pythons.items()
    }
    for future in cf.as_completed(jobs):
        name, spec = jobs[future]
        concept = course.concepts[name]
        status, out, err = future.result()
        # exact: a lesson and a question quote this output
        shown = concept.get("output", "").strip("\n")
        got = (out + (err if status else "")).strip("\n")
        if got != shown:
            report.error(
                26,
                f"{concept['_file']} {name}",
                f"witness prints {got[:60]!r} on {spec}, where the concept shows {shown[:60]!r}",
            )
    return len(jobs)
