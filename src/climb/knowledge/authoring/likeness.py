"""Rule 14: two questions explained alike, or carrying near-identical snippets,
and the `--near` listing of the pairs a reader should look at."""

import itertools
import math
import re
from collections import defaultdict

from climb.knowledge.authoring.course import Course, Question, Report

COMMON = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "what",
    "which",
    "does",
    "print",
    "prints",
    "when",
    "not",
    "are",
    "from",
    "its",
    "into",
    "than",
    "then",
    "you",
    "your",
    "how",
    "why",
    "can",
    "will",
    "has",
    "have",
    "one",
    "two",
    "after",
    "before",
    "each",
    "every",
    "only",
    "same",
    "new",
    "but",
    "use",
    "used",
    "using",
    "via",
    "per",
    "also",
    "both",
}
SAME_FACT = 0.65  # of the pairs explained this alike, about half ask one fact
CANDIDATE = 0.35  # holds half the pairs the review of 2026-11-11 named, among ten times as many


def tokens(code: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_]\w*|\d+|\S", re.sub(r"#.*", "", code)))


def similar(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def said(q: Question) -> list[str]:
    """The words a question explains its answer in, and the calls and dunder
    names among them. Two questions on one fact explain it alike, whatever
    their snippets and prompts look like."""
    # a mechanism derived from a concept is the same for every question on it
    mechanism = "" if "concept" in q else q["detail"]["mechanism"]
    text = " ".join([q.get("explain", ""), mechanism, *q.get("key", [])])
    plain = [w for w in re.findall(r"[a-z_][a-z_0-9]{2,}", text.lower()) if w not in COMMON]
    named = re.findall(r"[A-Za-z_][\w.]*(?=\()|__\w+__|\b[a-z_]+\.[a-z_.]+\b", text)
    return plain + ["`" + name for name in named]


def likeness(course: Course) -> dict[frozenset[str], float]:
    """How alike each two questions explain themselves, from 0 to 1: the
    cosine of their words, a word weighing more the fewer questions use it."""
    docs = {q["id"]: said(q) for q in course.questions}
    used: dict[str, int] = defaultdict(int)
    for text in docs.values():
        for word in set(text):
            used[word] += 1
    vectors: dict[str, dict[str, float]] = {}
    holders: dict[str, list[str]] = defaultdict(list)
    for qid, text in docs.items():
        count: dict[str, int] = defaultdict(int)
        for word in text:
            count[word] += 1
        v = {
            w: (1 + math.log(n)) * math.log(len(docs) / used[w])
            for w, n in count.items()
            if 1 < used[w] < 0.15 * len(docs)
        }
        length = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vectors[qid] = {w: x / length for w, x in v.items()}
        for w in v:
            holders[w].append(qid)
    alike: dict[frozenset[str], float] = defaultdict(float)
    for word, ids in holders.items():
        for a, b in itertools.combinations(ids, 2):
            alike[frozenset((a, b))] += vectors[a][word] * vectors[b][word]
    return alike


def recorded_pairs(course: Course) -> set[frozenset[str]]:
    recorded: set[frozenset[str]] = set()
    for cov in course.coverage.values():
        for sub in cov.get("subtopic", {}).values():
            for group in sub.get("duplicates", []):
                recorded |= {frozenset((a, b)) for a in group for b in group if a != b}
    return recorded | {frozenset(key.split(" ~ ")) for key in course.skip.get("same-fact", {})}


def near(course: Course, only: str) -> list[str]:
    """The pairs most alike first, for one id or above the candidate bar. Not
    a rule: at this bar most pairs ask two facts of one subject."""
    by_id = {q["id"]: q for q in course.questions}
    recorded = recorded_pairs(course)
    pairs = [
        (score, sorted(pair)) for pair, score in likeness(course).items() if pair not in recorded
    ]
    if only:
        pairs = sorted((p for p in pairs if only in p[1]), reverse=True)[:15]
    else:
        pairs = sorted((p for p in pairs if p[0] >= CANDIDATE), reverse=True)
    found: list[str] = []
    for score, (a, b) in pairs:
        a, b = (b, a) if b == only else (a, b)
        found.append(f"{score:.2f}  {_named(by_id[a])}  ~  {_named(by_id[b])}")
    return found


def _named(q: Question) -> str:
    return f"{q['id']} ({q['_sub']} L{q['level']})"


def overlaps(course: Course, report: Report) -> None:
    recorded = recorded_pairs(course)
    for pair, score in likeness(course).items():
        if score >= SAME_FACT and pair not in recorded:
            a, b = sorted(pair)
            report.warn(
                14,
                f"{a} ~ {b}",
                f"explained alike ({score:.2f}); one fact asked twice, "
                "or a pair for skip.same-fact",
            )
    coded = [
        (q, tokens(q["code"])) for q in course.questions if "code" in q and len(q["code"]) > 60
    ]
    for i, (a, ta) in enumerate(coded):
        for b, tb in coded[i + 1 :]:
            if similar(ta, tb) > 0.85 and frozenset((a["id"], b["id"])) not in recorded:
                report.warn(
                    14, f"{a['id']} ~ {b['id']}", "near-identical snippets, not in duplicates"
                )
