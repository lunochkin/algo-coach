"""The solver's two halves: extract a module's questions without their keys,
and score the solver's replies against the keys. SKILL.md gives the flow.

    solve.py extract <module dir> <out dir> [sub ...] [--all]
    solve.py score <out dir>
"""

import json
import random
import sys
import tomllib
from pathlib import Path

from climb.knowledge.authoring.course import norm

LETTERS = "ABCDEFGH"
# the module check proves these keys by running the code, rule 1
PROVEN = frozenset({"output", "debug"})


def extract(module: Path, out: Path, subs: list[str], every: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    asked, form, key = [], [], {}
    banks = sorted((module / "banks").glob("*/*.toml"))
    for path in banks:
        if subs and not {path.stem, f"{path.parent.name}/{path.stem}"} & set(subs):
            continue
        for q in tomllib.loads(path.read_text()).get("q", []):
            fmt = q.get("format", "choice")
            if fmt == "card":
                continue
            n = len(key) + 1
            item = {"n": n, "kind": q["kind"], "format": fmt, "prompt": q["prompt"]}
            if "code" in q:
                item["code"] = q["code"]
            entry = {"id": q["id"], "bank": f"{path.parent.name}/{path.stem}", "format": fmt}
            if fmt == "choice":
                rng = random.Random(q["id"])
                order = list(range(len(q["choices"])))
                rng.shuffle(order)
                item["choices"] = {LETTERS[i]: q["choices"][j] for i, j in enumerate(order)}
                item["pick"] = len(q["answer"])
                entry["key"] = sorted(LETTERS[order.index(ord(a) - 65)] for a in q["answer"])
                # the form pass sees the choices alone, under its own numbering
                form.append({"n": n, "choices": item["choices"], "pick": item["pick"]})
            else:
                entry["accept"] = q["accept"]
            if every or q["kind"] not in PROVEN:
                asked.append(item)
            key[n] = entry
    (out / "questions.json").write_text(json.dumps(asked, indent=1))
    (out / "form.json").write_text(json.dumps(form, indent=1))
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"{len(asked)} to answer, {len(form)} for the form pass, in {out}")


def score(out: Path) -> None:
    key = {int(n): e for n, e in json.loads((out / "key.json").read_text()).items()}
    replies = {r["n"]: r for r in json.loads((out / "replies.json").read_text())}
    forms = {r["n"]: r for r in json.loads((out / "form-replies.json").read_text())}
    lines: list[str] = []
    counts = {"differs": 0, "guessed": 0, "form": 0}
    for n, e in sorted(key.items()):
        r = replies.get(n)
        at = f"{e['bank']}:{e['id']}"
        # a question the answer pass skipped is judged by the form pass alone
        if r is not None:
            if e["format"] == "choice":
                right = sorted(r.get("pick", [])) == e["key"]
                said = ",".join(r.get("pick", []))
            else:
                right = norm(str(r.get("reply", ""))) in {norm(a) for a in e["accept"]}
                said = r.get("reply", "")
            if not right:
                counts["differs"] += 1
                lines.append(
                    f"- {at}: DIFFERS, replied {said!r} ({r.get('confidence')}): {r.get('reason')}"
                )
            elif r.get("confidence") == "guess":
                counts["guessed"] += 1
                lines.append(f"- {at}: GUESSED right: {r.get('reason')}")
        f = forms.get(n)
        if (
            f
            and e["format"] == "choice"
            and sorted(f.get("pick", [])) == e["key"]
            and f.get("confidence") != "guess"
        ):
            counts["form"] += 1
            lines.append(f"- {at}: FORM, key found from the choices alone: {f.get('reason')}")
    head = ", ".join(f"{v} {k}" for k, v in counts.items())
    report = f"# Solver findings\n\n{len(key)} questions: {head}.\n\n" + "\n".join(lines) + "\n"
    (out / "findings.md").write_text(report)
    print(report)


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    if command == "extract":
        rest = [a for a in args[2:] if a != "--all"]
        extract(Path(args[0]), Path(args[1]), rest, "--all" in args)
    else:
        score(Path(args[0]))
