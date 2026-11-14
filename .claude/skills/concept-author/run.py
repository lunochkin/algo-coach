"""Write a module's subtopics in the background, one headless session a step.

    run.py --level 0 [--jobs 1] [--only SUB ...] [--setup-only]

Each subtopic is written in a git worktree of the content repository, on a
branch of its own cut from the run's branch. `stages.py` takes it through
the concept-author skill's stages, each step a `claude -p` session. A
subtopic whose check passes is committed and merged into the run's branch,
which the author reviews by digest and merges to main.
Touch `<runs>/STOP` to start no new subtopic. SKILL.md `## Running in the
background` gives the rest.
"""

import argparse
import concurrent.futures as cf
import subprocess
import time
import tomllib
from pathlib import Path

import stages

ENGINE = Path(__file__).resolve().parents[3]
CONTENT = ENGINE / "content"
# the subtopic py already wrote under another slug than python's
RENAMED = {"functions-scope": "functions"}
# the model of each role. A stage 3 fix rewrites whole questions, and Haiku's
# left the next diff review its own faults to find.
MODELS = {
    "writer": "opus",
    "reviewer": "opus",
    "fixer": "haiku",
    "fixer3": "sonnet",
    "solver": "opus",
    "form": "haiku",
    "digest": "sonnet",
}


def git(*args: str, cwd: Path = CONTENT, check: bool = True) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and done.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.strip()


def plan(source: str) -> tuple[list[tuple[str, str, str]], dict[str, list[str]], dict[str, str]]:
    """Every subtopic of the source module, as (topic, slug, title), its needs,
    and each topic's title."""
    base = CONTENT / "modules" / source
    course = tomllib.loads((base / "course.toml").read_text())
    titles = {t["slug"]: (t.get("title", t["slug"]), t.get("tier", 1)) for t in course["topic"]}
    needs = tomllib.loads((base / "graph.toml").read_text()).get("needs", {})
    subs = [
        (t["slug"], RENAMED.get(s, s), t.get("sub_titles", {}).get(s, s))
        for t in course["topic"]
        for s in t["subs"]
    ]
    named = {RENAMED.get(k, k): [RENAMED.get(n, n) for n in v] for k, v in needs.items()}
    return subs, named, titles


def register(
    wt: Path, module: str, subs: list[tuple[str, str, str]], needs: dict, titles: dict
) -> None:
    """Name every subtopic in the module's course and graph before any job runs,
    so two jobs never edit the same line of either file."""
    base = wt / "modules" / module
    course = (base / "course.toml").read_text()
    have = tomllib.loads(course)
    known = {t["slug"]: t for t in have["topic"]}
    for topic in dict.fromkeys(t for t, _, _ in subs):
        mine = [(s, title) for t, s, title in subs if t == topic]
        if topic in known:
            new = [(s, title) for s, title in mine if s not in known[topic]["subs"]]
            if not new:
                continue
            old = "subs = [" + ", ".join(f'"{s}"' for s in known[topic]["subs"]) + "]"
            subs_line = (
                "subs = ["
                + ", ".join(f'"{s}"' for s in known[topic]["subs"] + [s for s, _ in new])
                + "]"
            )
            course = course.replace(old, subs_line, 1)
            head = "[topic.sub_titles]\n"
            at = course.index(head, course.index(f'slug = "{topic}"')) + len(head)
            course = course[:at] + "".join(f'"{s}" = "{t}"\n' for s, t in new) + course[at:]
        else:
            course += (
                f'\n[[topic]]\nslug = "{topic}"\ntier = {titles[topic][1]}\n'
                + f'title = "{titles[topic][0]}"\n'
                + "subs = ["
                + ", ".join(f'"{s}"' for s, _ in mine)
                + "]\n\n[topic.sub_titles]\n"
                + "".join(f'"{s}" = "{t}"\n' for s, t in mine)
            )
    (base / "course.toml").write_text(course)
    graph = (base / "graph.toml").read_text()
    present = tomllib.loads(graph).get("needs", {})
    lines = "".join(
        f'"{s}" = [' + ", ".join(f'"{n}"' for n in needs[s]) + "]\n"
        for _, s, _ in subs
        if s in needs and s not in present
    )
    at = graph.index("[needs]\n") + len("[needs]\n")
    (base / "graph.toml").write_text(graph[:at] + lines + graph[at:])


def write(args: argparse.Namespace, topic: str, sub: str, title: str) -> str:
    runs: Path = args.runs
    name = f"{sub}-L{args.level}"
    branch = f"{args.branch}-{name}"
    wt, scratch = runs / "wt" / name, runs / "scratch" / name
    if not wt.exists():
        git("worktree", "add", "-B", branch, str(wt), args.branch)
    if (scratch / "progress.md").exists() and not (scratch / "state.json").exists():
        # a session of the one-session runner left this: keep its concepts alone
        scratch.rename(scratch.with_name(f"{name}-old"))
    scratch.mkdir(parents=True, exist_ok=True)
    job = stages.Job(
        engine=ENGINE,
        module=args.module,
        topic=topic,
        sub=sub,
        title=title,
        level=args.level,
        wt=wt,
        scratch=scratch,
        log=runs / "logs" / f"{name}.log",
        models={k: getattr(args, k) for k in MODELS},
        hours=args.hours,
        shadow=args.shadow,
    )
    concepts = wt / "modules" / args.module / "concepts" / topic / f"{sub}.toml"
    if concepts.exists() and not job.state():
        job.mark("s1-write")
    try:
        if not stages.run(job, args.stop_after):
            return f"{sub}: STOPPED after stage {args.stop_after}"
    except stages.Failed as error:
        return f"{sub}: FAILED: {error}"
    digest = wt / "modules" / args.module / "review" / f"{topic}-{sub}-L{args.level}.md"
    first = digest.read_text().splitlines()[0] if digest.exists() else "FAILED: no digest"
    if not first.startswith("DONE"):
        return f"{sub}: {first}"
    git("add", f"modules/{args.module}", cwd=wt)
    git(
        "commit",
        "-q",
        "-m",
        f"feat({args.module}): write {topic}/{sub} at level {args.level}",
        cwd=wt,
    )
    return f"{sub}: DONE"


def setup(args: argparse.Namespace) -> tuple[Path, list[tuple[str, str, str]], dict]:
    """The run's branch and worktree, every subtopic named in the module."""
    if not git("branch", "--list", args.branch):
        git("branch", args.branch, "main")
    main_wt = args.runs / "wt" / "integration"
    if not main_wt.exists():
        git("worktree", "add", str(main_wt), args.branch)
    subs, needs, titles = plan(args.source)
    register(main_wt, args.module, subs, needs, titles)
    # two jobs append lessons to the end of one graph.toml
    attributes = main_wt / ".gitattributes"
    rule = f"modules/{args.module}/graph.toml merge=union\n"
    if rule not in (attributes.read_text() if attributes.exists() else ""):
        with attributes.open("a") as f:
            f.write(rule)
    if git("status", "--porcelain", cwd=main_wt):
        git("add", ".gitattributes", f"modules/{args.module}", cwd=main_wt)
        git("commit", "-q", "-m", f"chore({args.module}): name the subtopics to write", cwd=main_wt)
    return main_wt, subs, needs


def schedule(args: argparse.Namespace, main_wt: Path, subs: list, needs: dict) -> None:
    """Start each subtopic once those it needs are merged, `jobs` at once."""
    report = args.runs / f"report-L{args.level}.md"
    review = main_wt / "modules" / args.module / "review"
    done = {p.stem.rsplit("-L", 1)[0].split("-", 1)[1] for p in review.glob(f"*-L{args.level}.md")}
    # the pilot wrote these at levels 0 and 1 by hand
    finished = done | ({"control-flow", "functions"} if args.level <= 1 else set())
    known = {s for _, s, _ in subs}
    todo = [x for x in subs if x[1] not in finished and (not args.only or x[1] in args.only)]
    failed: set[str] = set()
    running: dict[cf.Future[str], str] = {}

    def log(line: str) -> None:
        with report.open("a") as f:
            f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} {line}\n")
        print(line, flush=True)

    with cf.ThreadPoolExecutor(args.jobs) as pool:
        while todo or running:
            for x in [x for x in todo if failed & set(needs.get(x[1], []))]:
                todo.remove(x)
                failed.add(x[1])
                log(f"{x[1]}: SKIPPED, a subtopic it needs failed")
            ready = [x for x in todo if set(needs.get(x[1], [])) & known <= finished]
            while ready and len(running) < args.jobs and not (args.runs / "STOP").exists():
                x = ready.pop(0)
                todo.remove(x)
                running[pool.submit(write, args, *x)] = x[1]
            if not running:
                break
            for f in cf.wait(running, return_when=cf.FIRST_COMPLETED)[0]:
                sub = running.pop(f)
                try:
                    line = f.result()
                except Exception as error:  # a job's crash fails that subtopic alone
                    line = f"{sub}: FAILED: {error}"
                if line.endswith("DONE"):
                    branch = f"{args.branch}-{sub}-L{args.level}"
                    git("merge", "-q", "--no-ff", "--no-edit", branch, cwd=main_wt)
                    finished.add(sub)
                else:
                    failed.add(sub)
                log(line)
    print(f"report: {report}")


def cwd_of(pid: str) -> Path | None:
    out = subprocess.run(
        ["lsof", "-a", "-d", "cwd", "-Fn", "-p", pid], capture_output=True, text=True
    )
    paths = [line[1:] for line in out.stdout.splitlines() if line.startswith("n")]
    return Path(paths[0]) if paths else None


def status(args: argparse.Namespace) -> None:
    """One line per subtopic: its state, its last progress line, and its last
    activity, a silent one flagged."""
    subs, _, _ = plan(args.source)
    report = args.runs / f"report-L{args.level}.md"
    states = {}
    for line in report.read_text().splitlines() if report.exists() else []:
        sub, _, verdict = line.split(" ", 3)[-1].partition(": ")
        states[sub] = verdict.split(":")[0]
    sessions = subprocess.run(["pgrep", "-f", "claude -p"], capture_output=True, text=True)
    now = time.time()
    for topic, sub, _ in subs:
        name = f"{sub}-L{args.level}"
        scratch, log = args.runs / "scratch" / name, args.runs / "logs" / f"{name}.log"
        # a session runs in its subtopic's worktree; its prompt names others
        live = sessions.stdout and any(
            cwd_of(pid) == args.runs / "wt" / name for pid in sessions.stdout.split()
        )
        state = "running" if live else states.get(sub, "queued").lower()
        files = [p for p in [log, *scratch.rglob("*")] if p.is_file()]
        if not files and state == "queued":
            continue
        quiet = (now - max(p.stat().st_mtime for p in files)) / 60 if files else 0
        progress = scratch / "progress.md"
        last = progress.read_text().splitlines()[-1] if progress.exists() else "-"
        flag = "  SILENT" if state == "running" and quiet > 20 else ""
        print(f"{topic}/{sub:24} {state:8} {quiet:5.0f} min ago  {last}{flag}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--module", default="py")
    p.add_argument("--source", default="python")
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--hours", type=float, default=1, help="the limit on one step")
    for role, model in MODELS.items():
        p.add_argument(f"--{role}", default=model)
    p.add_argument("--branch", default="py-auto")
    p.add_argument("--runs", type=Path, default=ENGINE.parent / "py-runs")
    p.add_argument("--only", nargs="*", default=[])
    p.add_argument("--setup-only", action="store_true")
    p.add_argument("--shadow", action="store_true", help="run each review again as shadow.py gives")
    p.add_argument("--stop-after", type=int, default=3, help="the last stage, for a trial")
    p.add_argument("--status", action="store_true")
    args = p.parse_args()
    (args.runs / "logs").mkdir(parents=True, exist_ok=True)
    if args.status:
        return status(args)
    main_wt, subs, needs = setup(args)
    if not args.setup_only:
        schedule(args, main_wt, subs, needs)


if __name__ == "__main__":
    main()
