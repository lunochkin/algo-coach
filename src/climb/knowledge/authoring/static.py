"""The rules read from the files alone, with no snippet run: 3, 6, 8, 10, 13,
17, 18, 19 and 21, and the kinds the seed refuses too."""

import importlib.metadata
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from climb.knowledge.authoring.course import Course, Report, fmt, where

LEAN = re.compile(r"\b(also|too|instead)\b", re.I)
OPENER = re.compile(r"^(It|This|That|These|Those|Also|Both|Its|Their|They)\b")
POSITIONAL = re.compile(
    r"\b(choice|option) [A-H]\b"
    r"|\b(the|see) (first|second|third|fourth|fifth|last) (choice|option)\b"
)
BINARY = frozenset({"true", "false", "yes", "no"})
# a choice's parts: a bracketed or quoted group whole, else a word
PART = re.compile(r"\[[^\]]*\]|\([^)]*\)|'[^']*'|\"[^\"]*\"|[^\s,]+")
FILLER = frozenset({"then", "at", "the", "a", "an", "of", "is", "and"})
VERDICT = re.compile(r"^(Right|Wrong|Correct|Incorrect)\b[:.,]", re.I)
IGNORED_SECTIONS = {
    "go-deeper",
    "common-mistakes",
    "further-reading",
    "docs",
    "see-also",
    "summary",
    "why-it-matters",
}


def choices(course: Course, report: Report) -> None:
    """Rule 8: at least two wrong options. Rule 10: the keyed choice is not
    the longest by far."""
    for q in course.questions:
        if fmt(q) != "choice":
            continue
        wrong = len(q["choices"]) - len(q["answer"])
        if len(q["answer"]) > 1 and wrong < 2:
            report.error(8, where(q), f"choose {len(q['answer'])} of {len(q['choices'])}")
        if len(q["answer"]) == 1:
            sizes = [len(c) for c in q["choices"]]
            at = ord(q["answer"][0]) - 65
            keyed, rest = sizes[at], max(s for i, s in enumerate(sizes) if i != at)
            if keyed > 1.3 * rest and keyed - rest > 15:
                report.warn(10, where(q), f"keyed choice {keyed} chars, longest other {rest}")


def replies(course: Course, report: Report) -> None:
    """Rule 3, in a module written by concept: a `short` reply of only true or
    false, or yes or no, is a guess."""
    for q in course.questions:
        if fmt(q) == "short" and {a.strip().lower() for a in q["accept"]} <= BINARY:
            report.error(3, where(q), "the reply is a yes or no, so the format is choice")


def verdicts(course: Course, report: Report) -> None:
    """Rule 12, in a module written by concept: the client marks each choice
    right or wrong, so a `why` opening with the verdict repeats it."""
    for q in course.questions:
        if fmt(q) == "choice" and any(VERDICT.match(w) for w in q["why"]):
            report.warn(12, where(q), "a why opens with its verdict, which the client shows")


def centres(course: Course, report: Report) -> None:
    """Rule 10, in a module written by concept: a key built as the choice each
    distractor varies by one part is found from the choices alone."""
    for q in course.questions:
        if fmt(q) != "choice" or len(q["answer"]) != 1 or len(q["choices"]) < 3:
            continue
        parts = [_parts(c) for c in q["choices"]]
        if min(map(len, parts)) == 0 or max(map(len, parts)) < 2:
            continue
        key = ord(q["answer"][0]) - 65
        shared = [[_shared(a, b) for b in parts] for a in parts]
        score = [sum(row) - row[i] for i, row in enumerate(shared)]
        rivals = [score[i] for i in range(len(parts)) if i != key]
        if all(shared[key][i] for i in range(len(parts)) if i != key) and score[key] > max(rivals):
            report.warn(10, where(q), "the key shares a part with every other choice, the most")


def _parts(choice: str) -> list[str]:
    # a tuple or a list is compared item by item: "(2, None)", "(0, None)"
    found: list[str] = []
    for part in PART.findall(choice):
        if part[:1] in "([" and part[-1:] in ")]":
            found += [x.strip() for x in part[1:-1].split(",") if x.strip()]
        elif part.lower() not in FILLER:
            found.append(part)
    return found


def _shared(a: list[str], b: list[str]) -> int:
    # one shape varies by position: "True False" against "False True"
    if len(a) == len(b):
        return sum(x == y for x, y in zip(a, b, strict=True))
    return sum((Counter(a) & Counter(b)).values())


def positions(course: Course, report: Report) -> None:
    """Rule 10: choices are shuffled, so prose may not name one by its
    position."""
    for q in course.questions:
        prose = [
            q.get("explain", ""),
            *q.get("why", []),
            *q.get("key_detail", []),
            *q.get("traps_detail", []),
        ]
        for value in q.get("detail", {}).values():
            prose += value if isinstance(value, list) else [value]
        for text in prose:
            if m := POSITIONAL.search(text):
                report.error(10, where(q), f"names a choice by position: {m[0]!r}")


def library_versions(course: Course, report: Report) -> None:
    """Rule 6: a library version named in a prompt is the installed one."""
    installed: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        # the first on sys.path is the one an import gets
        name = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
        installed.setdefault(name, dist.version)
    names = "|".join(
        sorted((re.escape(n).replace("\\-", "[-_. ]?") for n in installed), key=len, reverse=True)
    )
    named = re.compile(rf"(?<![\w.-])({names}) v?(\d+(?:\.\d+)*)(?![\w-])", re.I)
    for q in course.questions:
        if q["id"] in course.skip.get("library-version", {}):
            continue
        for m in named.finditer(q["prompt"]):
            have = installed.get(re.sub(r"[-_. ]+", "-", m[1]).lower())
            if have and not (have + ".").startswith(m[2] + "."):
                report.error(6, where(q), f"prompt names {m[1]} {m[2]}, and {have} is installed")


def kinds(course: Course, report: Report) -> None:
    """The seed refuses these too, and the pre-commit hook catches them
    before a seed."""
    allowed, coded = course.settings.get("kinds", []), course.settings.get("code_kinds", [])
    for q in course.questions:
        if allowed and q["kind"] not in allowed:
            report.error(1, where(q), f"kind {q['kind']!r} is none of {allowed}")
        if q["kind"] in coded and not q.get("code", "").strip():
            report.error(1, where(q), f"a {q['kind']} question carries no code")


def open_questions(course: Course, report: Report) -> None:
    """Rule 13: an open question's key points."""
    for q in course.questions:
        if fmt(q) != "card":
            continue
        key, detail = q["key"], q.get("key_detail", [])
        if not 3 <= len(key) <= 4:
            report.error(13, where(q), f"{len(key)} key points")
        if detail and len(detail) != len(key):
            report.error(13, where(q), f"{len(detail)} key_detail entries for {len(key)} points")
        for point in key:
            if len(point) > 100:
                report.error(13, where(q), f"point over 100 chars: {point[:50]}…")
            if OPENER.match(point) or LEAN.search(point):
                report.error(13, where(q), f"point leans on another: {point[:50]}…")


def anchor(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def _prose(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def lesson_links(course: Course, report: Report) -> None:
    """Rule 17: a question's level against its lesson's. Rule 18: a link to a
    lesson or section that does not exist, and a section nobody points at."""
    pointed: dict[str, set[str]] = defaultdict(set)
    for q in course.questions:
        slug, _, at = q["lesson"].partition("#")
        pointed[slug].add(at)
        levels = _taught(course, slug, q["_sub"]) if slug in course.graph["lesson"] else []
        if levels and q["level"] < min(levels):
            report.error(17, where(q), f"L{q['level']} question in an L{min(levels)} lesson")
    heads_of = {
        slug: {anchor(t) for _, t in re.findall(r"^(#{1,3}) (.+)$", _prose(text), re.M)}
        for slug, text in course.lessons.items()
    }
    for source, text in course.lessons.items():
        for slug, at in re.findall(r"\(lesson:([\w-]+)(?:#([\w-]+))?\)", text):
            if slug not in heads_of:
                report.error(
                    18, f"lessons/{source}.md", f"links lesson:{slug}, which does not exist"
                )
            elif at and at not in heads_of[slug]:
                report.error(
                    18,
                    f"lessons/{source}.md",
                    f"links lesson:{slug}#{at}, a section that does not exist",
                )
            pointed[slug].add(at)
    for slug, text in course.lessons.items():
        for at in _unpointed(_prose(text), pointed[slug]):
            report.warn(18, f"lessons/{slug}.md", f"no question points at #{at}")


def _taught(course: Course, slug: str, sub: str) -> list[int]:
    teaches = course.graph["lesson"][slug]["teaches"]
    return [int(t.split("@")[1]) for t in teaches if t.split("@")[0] == sub]


def _unpointed(body: str, pointed: set[str]) -> list[str]:
    """The sections no question or link points at, nor at any section under."""
    heads = [(len(h), anchor(t)) for h, t in re.findall(r"^(#{2,3}) (.+)$", body, re.M)]
    found: list[str] = []
    for i, (depth, at) in enumerate(heads):
        children: list[str] = []
        for d, a in heads[i + 1 :]:
            if d <= depth:
                break
            children.append(a)
        if at not in pointed and not set(children) & pointed and at not in IGNORED_SECTIONS:
            found.append(at)
    return found


def coverage(course: Course, report: Report) -> None:
    """Rule 19: every concept covered at its own level, and every question
    filed."""
    levels = {q["id"]: q["level"] for q in course.questions}
    filed: set[str] = set()
    for topic, cov in course.coverage.items():
        for sub_name, sub in cov.get("subtopic", {}).items():
            for concept in sub.get("concept", []):
                at = f"coverage/{topic}.toml {sub_name}/{concept['id']}"
                ids = concept.get("covered_by", [])
                filed |= set(ids)
                if unknown := [i for i in ids if i not in levels]:
                    report.error(19, at, f"unknown ids {unknown}")
                if not any(levels.get(i) == concept["level"] for i in ids):
                    report.error(19, at, f"no question at L{concept['level']}")
    for q in course.questions:
        if q["id"] not in filed:
            report.error(19, where(q), "filed under no concept")


def _git(repo: Path, *argv: str, check: bool = False) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *argv], capture_output=True, text=True, check=check
    )
    return done.stdout


def reused_ids(course: Course, report: Report) -> None:
    """Rule 21: no id that history retired is in a bank again, and no id is
    used twice."""
    root = course.root.resolve()
    repo = Path(_git(root, "rev-parse", "--show-toplevel", check=True).strip()).resolve()
    banks = str(root.relative_to(repo) / "banks")
    lines = _git(repo, "rev-list", "--parents", "HEAD", "--", banks, check=True).splitlines()
    ids: dict[str, set[str]] = {}

    def held(commit: str) -> set[str]:
        if commit not in ids:
            text = _git(repo, "grep", "-h", "-o", r'^id = "[^"]*"', commit, "--", banks)
            ids[commit] = set(re.findall(r'"([^"]*)"', text))
        return ids[commit]

    # an id is retired where a commit drops it from one of its own parents: a
    # branch cut before the id was written never held it
    retired: set[str] = set()
    for line in lines:
        commit, *parents = line.split()
        for parent in parents:
            retired |= held(parent) - held(commit)
    for q in course.questions:
        if q["id"] in retired:
            report.error(21, where(q), "reuses an id a past commit retired")
    counts: dict[str, int] = defaultdict(int)
    for q in course.questions:
        counts[q["id"]] += 1
    for qid, n in counts.items():
        if n > 1:
            report.error(21, qid, f"id used {n} times")
