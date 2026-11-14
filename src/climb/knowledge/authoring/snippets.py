"""Rules 1, 3 and 5: a question's snippet prints its keyed answer, and prints
the same on every supported version and build unless its prompt names one."""

import concurrent.futures as cf
import re
import subprocess
from collections import defaultdict

from climb.knowledge.authoring.course import Course, Question, Report, fmt, norm, where
from climb.knowledge.authoring.execution import (
    WARNED,
    Ran,
    Runs,
    absent,
    last_exception,
    raised_by,
    third_party,
)

TOOLS = re.compile(r"\b(mypy|pyright|ruff|reveal_type|pytest)\b")
VERSION = re.compile(r"\b3\.(\d{1,2})\b")
BUILD = re.compile(r"free-thread|\bGIL\b|\b3\.\d+t\b|default build", re.I)

# what a run showed, comparable between interpreters
type Outcome = tuple[str, str, str]


def runnable(q: Question, course: Course, rule: str, report: Report) -> bool:
    return (
        "code" in q
        and q["id"] not in course.skip.get(rule, {})
        and not TOOLS.search(q["prompt"] + q["code"])
        and not absent(q["code"], course, report)
    )


def lines(text: str) -> str:
    """Output comparable with a choice: `a, then b`, `a / b` or `a; b`."""
    return re.sub(r"\bthen\b|[\s,;/'\"`]", "", text).lower()


def shares(out: str, choice: str) -> bool:
    """Whether a choice shows the output: every printed line in its order,
    the choice free to add words around them, as `twice` or a reason does."""
    got, said = [lines(x) for x in out.strip().splitlines() if x.strip()], lines(choice)
    at = 0
    for line in got:
        at = said.find(line, at)
        if at < 0:
            return False
        at += len(line)
    return bool(got)


def in_zone(q: Question) -> str:
    """A snippet whose prompt names the process's time zone, run in that
    zone."""
    if m := re.search(r"\bTZ=([\w/+-]+)", q["prompt"]):
        return f"import os, time\nos.environ['TZ'] = {m[1]!r}\ntime.tzset()\n" + q["code"]
    return q["code"]


def outcome(status: int, out: str, err: str) -> Outcome:
    """The output, the exception's name and the warnings' names. Their wording
    differs by version."""
    raised = "timeout" if status == -1 else last_exception(err) if status else ""
    return norm(out), raised, " ".join(sorted(set(WARNED.findall(err))))


def snippets(course: Course, report: Report, pool: cf.Executor, runs: Runs) -> dict[str, Outcome]:
    jobs: dict[cf.Future[Ran], Question] = {}
    for q in course.questions:
        if q["kind"] != "output" or not runnable(q, course, "snippet", report):
            continue
        if fmt(q) in ("short", "choice"):
            jobs[pool.submit(runs.run, in_zone(q))] = q
    seen_here: dict[str, Outcome] = {}
    for future in cf.as_completed(jobs):
        q = jobs[future]
        code, out, err = future.result()
        seen_here[q["id"]] = outcome(code, out, err)
        if code == -1:
            report.error(1, where(q), "snippet timed out")
        else:
            _judge(q, course, report, (code, out, err))
    return seen_here


def _judge(q: Question, course: Course, report: Report, ran: Ran) -> None:
    code, out, err = ran
    seen = {norm(out), norm(out.strip().splitlines()[-1]) if out.strip() else ""}
    if code:
        seen.add(norm(last_exception(err)))
    if out.strip():
        seen.add(norm(re.split(r"[\s:]", out.strip())[0]))
    seen.discard("")
    if fmt(q) == "short":
        if not seen & {norm(a) for a in q["accept"]}:
            report.error(3, where(q), f"output {out.strip()[:60]!r} matches no accepted answer")
        return
    keyed = {norm(q["choices"][ord(a) - 65]) for a in q["answer"]}
    others = {norm(c) for i, c in enumerate(q["choices"]) if chr(65 + i) not in q["answer"]}
    whole = norm(out) if not code else norm(last_exception(err))
    if whole in others and whole not in keyed:
        report.error(1, where(q), f"output {out.strip()[:60]!r} matches an unkeyed choice")
        return
    shows = [
        chr(65 + i)
        for i, c in enumerate(q["choices"])
        if shares(out + raised_by(code, err), c) or shares(out + err, c)
    ]
    if set(shows) & set(q["answer"]) or (seen | {whole}) & keyed:
        return
    skipped = q["id"] in course.skip.get("choice-match", {})
    if (shows or (seen | {whole}) & others) and not skipped:
        wrong = ", ".join(shows) or "an unkeyed choice"
        report.error(1, where(q), f"output {out.strip()[:60]!r} is shown by {wrong}, not the key")
        return
    if not out.strip() and raised_by(code, err) in ("NameError", "SyntaxError"):
        report.fragments += 1  # code its prompt completes: a model, an engine, a file
    elif not skipped:
        printed = (out or last_exception(err)).strip()[:60]
        report.warn(1, where(q), f"output {printed!r} matches no choice")


def find(spec: str, report: Report) -> str | None:
    """The interpreter a check.toml entry names: `3.13`, or `3.15t` for the
    free-threaded build. The GIL build is asked for by name, since uv
    otherwise prefers a free-threaded one it manages."""
    request = f"{spec[:-1]}+freethreaded" if spec.endswith("t") else f"{spec}+gil"
    done = subprocess.run(["uv", "python", "find", request], capture_output=True, text=True)
    if done.returncode:
        report.error(
            5, "check.toml", f"no Python {spec} to compare against: uv python install {spec}"
        )
        return None
    return done.stdout.strip()


def versions(
    course: Course, report: Report, pool: cf.Executor, runs: Runs, here: dict[str, Outcome]
) -> int:
    pythons = {
        spec: python for spec in course.versions + course.builds if (python := find(spec, report))
    }
    skipped = course.skip.get("versions", {})
    # a debug or concept snippet has no keyed output to hold, and still may not
    # change by version
    rest = {
        pool.submit(runs.run, q["code"]): q
        for q in course.questions
        if q["id"] not in here
        and q["id"] not in skipped
        and runnable(q, course, "snippet", report)
        and not third_party(q["code"])
    }
    unkeyed = {q["id"] for q in rest.values()}
    here = here | {q["id"]: outcome(*future.result()) for future, q in rest.items()}
    swept = [
        q
        for q in course.questions
        if q["id"] in here and q["id"] not in skipped and not third_party(q["code"])
    ]
    jobs = {
        pool.submit(runs.run, in_zone(q), python): (q, spec)
        for q in swept
        for spec, python in pythons.items()
    }
    differs: dict[str, list[str]] = defaultdict(list)
    hung: set[tuple[str, str]] = set()
    for future in cf.as_completed(jobs):
        q, spec = jobs[future]
        if outcome(*future.result()) != here[q["id"]]:
            differs[q["id"]].append(spec)
            if future.result()[0] == -1:
                hung.add((q["id"], spec))
    for q in swept:
        _versioned(q, course, report, differs[q["id"]], hung)
        if _needless(q, course, here, unkeyed, differs[q["id"]]):
            named = min(int(m) for m in VERSION.findall(q["prompt"]))
            report.warn(
                5,
                where(q),
                f"prompt names 3.{named}, and the output is the same on every supported version",
            )
    return len(jobs) + expected(course, report, pool, runs)


def _versioned(
    q: Question, course: Course, report: Report, differs: list[str], hung: set[tuple[str, str]]
) -> None:
    named = [int(m) for m in VERSION.findall(q["prompt"])]
    older = sorted(int(spec.split(".")[1]) for spec in differs if spec in course.versions)
    late = [m for m in older if not named or m >= min(named)]
    # a kept timeout may have been the machine's load, so the finding says how
    # to measure again
    timed_out = late and (q["id"], f"3.{late[0]}") in hung
    what = "times out (--fresh measures again)" if timed_out else "prints something else"
    if late and not named:
        report.error(5, where(q), f"{what} on 3.{late[0]}, and the prompt names no version")
    elif late:
        report.error(
            5, where(q), f"{what} on 3.{late[0]}, which the prompt's 3.{min(named)} covers"
        )
    for spec in differs:
        if spec in course.builds and not BUILD.search(q["prompt"]):
            report.warn(
                5,
                where(q),
                f"prints something else on the free-threaded {spec}, and the prompt names no build",
            )


def _needless(
    q: Question, course: Course, here: dict[str, Outcome], unkeyed: set[str], differs: list[str]
) -> bool:
    """A version the prompt names, where no supported version differs."""
    return bool(
        VERSION.findall(q["prompt"])
        and not any(spec in course.versions for spec in differs)
        and not here[q["id"]][1]
        and q["id"] not in unkeyed
        and course.versions
        and not BUILD.search(q["prompt"])
    )


def expected(course: Course, report: Report, pool: cf.Executor, runs: Runs) -> int:
    """Rule 5: an answer keyed for another build is what that build prints."""
    by_id = {q["id"]: q for q in course.questions}
    jobs: dict[cf.Future[Ran], tuple[str, str, str]] = {}
    for spec, outputs in course.expect.items():
        if python := find(spec, report):
            for qid, output in outputs.items():
                jobs[pool.submit(runs.run, by_id[qid]["code"], python)] = (qid, spec, output)
    for future in cf.as_completed(jobs):
        qid, spec, output = jobs[future]
        got = future.result()[1]
        if norm(got) != norm(output):
            report.error(
                5,
                where(by_id[qid]),
                f"check.toml expects {output!r} on {spec}, got {got.strip()[:60]!r}",
            )
    return len(jobs)
