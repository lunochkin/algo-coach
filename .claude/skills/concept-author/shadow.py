"""The shadow test: each review run again under a candidate setting, and a
judge counting the reference review's findings the candidate missed. The
reference review alone decides the run."""

import concurrent.futures as cf
import json
import sys
from pathlib import Path

# name, model (None: the reference's), effort, and whether it reviews this
# round. The baseline is a second reference review: what it misses is the
# noise between two reviews, which a candidate's misses are read against.
CANDIDATES = [
    ("baseline", None, None, lambda stage, kind: True),
    ("sonnet", "sonnet", None, lambda stage, kind: kind == "diff" or stage > 1),
]


def reviews(job, n: int, r: int, kind: str, given: str, scope: str, report: Path) -> None:
    folder = report.parent
    chosen = [c for c in CANDIDATES if c[3](n, kind)]

    def one(name: str, model: str | None, effort: str | None) -> None:
        mine = folder / f"review-{r}.{name}.md"
        step = f"stage {n} review {r} ({kind}) shadow {name}"
        log = job.log.with_suffix(f".{name}.log")
        model = model or job.models["reviewer"]
        job.session(
            "review",
            model,
            step,
            given=given,
            effort=effort,
            log=log,
            stage=n,
            scope=scope,
            report=mine,
            cases=mine.with_name(f"{mine.stem}-cases.py"),
        )
        if mine.exists():
            out = folder / f"review-{r}.{name}.json"
            job.session("judge", "sonnet", f"{step} judge", log=log, a=report, b=mine, out=out)

    with cf.ThreadPoolExecutor(len(chosen)) as pool:
        for done in [pool.submit(one, *c[:3]) for c in chosen]:
            done.result()
    job.progress(f"stage {n} review {r}: shadow {', '.join(c[0] for c in chosen)} done")


def summary(scratch: Path) -> None:
    """Per candidate: the reference's findings it missed, and its cost against
    the reference reviews it shadowed."""
    totals: dict[str, dict[str, float]] = {}
    for folder in sorted(scratch.iterdir()):
        costs: dict[str, float] = {}
        tokens = folder / "tokens.tsv"
        for line in tokens.read_text().splitlines() if tokens.exists() else []:
            step, _, *_, cost = line.split("\t")
            costs[step] = costs.get(step, 0) + float(cost)
        for found in folder.glob("stage*/review-*.*.json"):
            name = found.stem.split(".", 1)[1]
            stage, r = found.parent.name[5:], found.stem.split(".")[0].split("-")[1]
            t = totals.setdefault(
                name,
                dict.fromkeys(
                    [
                        "rounds",
                        "wrong",
                        "wrong_missed",
                        "defect",
                        "defect_missed",
                        "b_only",
                        "cost",
                        "ref",
                    ],
                    0.0,
                ),
            )
            judged = json.loads(found.read_text())
            t["rounds"] += 1
            for k in ("wrong", "wrong_missed", "defect", "defect_missed", "b_only"):
                t[k] += judged.get(k, 0)
            for step, cost in costs.items():
                if step.startswith(f"stage {stage} review {r} ("):
                    if step.endswith(f"shadow {name}"):
                        t["cost"] += cost
                    elif "shadow" not in step:
                        t["ref"] += cost
    for name, t in totals.items():
        print(
            f"{name}: {t['rounds']:.0f} reviews; "
            f"missed {t['wrong_missed']:.0f} of {t['wrong']:.0f} WRONG, "
            f"{t['defect_missed']:.0f} of {t['defect']:.0f} DEFECT; {t['b_only']:.0f} of its own; "
            f"cost ${t['cost']:.2f} against ${t['ref']:.2f}"
        )


if __name__ == "__main__":
    summary(Path(sys.argv[1]))
