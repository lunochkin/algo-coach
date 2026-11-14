"""One subtopic through the three stages, one headless session per step.

The run holds the order and the stopping rule of concepts.md `## Stages`, so
no session carries the context of the steps before it.
"""

import datetime
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import inputs
import shadow

BRIEFS = Path(__file__).parent / "briefs"
MAX_FULL = 2
MAX_ROUNDS = 6
COUNTS = re.compile(r"^COUNTS WRONG=(\d+) DEFECT=(\d+) STYLE=(\d+)")
LAYERS = {
    1: "the concept file concepts/{topic}/{sub}.toml, the lesson files graph.toml names "
    "for this subtopic as headings alone, and the subtopic's entries in course.toml "
    "and graph.toml",
    2: "the lesson files graph.toml names for this subtopic",
    3: "the bank banks/{topic}/{sub}.toml",
}


class Failed(Exception):
    pass


@dataclass
class Job:
    engine: Path
    module: str
    topic: str
    sub: str
    title: str
    level: int
    wt: Path
    scratch: Path
    log: Path
    models: dict[str, str]
    hours: float
    # run each review again under the candidate settings, for comparison alone
    shadow: bool = False

    @property
    def state_file(self) -> Path:
        return self.scratch / "state.json"

    def state(self) -> dict:
        return json.loads(self.state_file.read_text()) if self.state_file.exists() else {}

    def mark(self, key: str, value: object = True) -> None:
        state = self.state() | {key: value}
        self.state_file.write_text(json.dumps(state, indent=1))

    def progress(self, line: str) -> None:
        with (self.scratch / "progress.md").open("a") as f:
            f.write(f"{time.strftime('%H:%M')} {line}\n")

    def fields(self, **extra: object) -> dict:
        return {
            "topic": self.topic,
            "sub": self.sub,
            "title": self.title,
            "module": self.module,
            "level": self.level,
            "engine": self.engine,
            "wt": self.wt,
            "scratch": self.scratch,
            # the run's one list of questions on rules, skills and the engine
            "shared": self.scratch.parent.parent / f"author-L{self.level}.md",
        } | extra

    def fixer(self, stage: int) -> str:
        return self.models.get(f"fixer{stage}", self.models["fixer"])

    def given(self, role: str, stage: int, extra: list[Path] | None = None) -> str:
        module = self.wt / "modules" / self.module
        return inputs.given(self.engine, module, self.topic, self.sub, role, stage, extra or [])

    def session(
        self,
        brief: str,
        model: str,
        step: str,
        given: str = "",
        effort: str | None = None,
        log: Path | None = None,
        **extra: object,
    ) -> None:
        # a session running beside another needs its own log: each reads its
        # result from the events appended after its start
        log = log or self.log
        f = self.fields(**extra)
        text = (BRIEFS / f"{brief}.md").read_text().format(**f)
        # the solver's agents and the judge read their own files alone
        if brief not in ("solve", "form", "judge"):
            text = (BRIEFS / "common.md").read_text().format(**f) + text + given
        while True:
            start = log.stat().st_size if log.exists() else 0
            with log.open("a") as out:
                out.write(f"\n### {time.strftime('%F %T')} {step} ({model})\n")
                out.flush()
                subprocess.run(
                    ["claude", "-p", text, "--model", model, "--permission-mode", "auto"]
                    # no MCP server and no user settings: 9k tokens to start,
                    # against 46k in the engine
                    + ["--strict-mcp-config", "--setting-sources", "project,local"]
                    + ["--add-dir", str(self.engine)]
                    # the four tools a step uses; the rest cost 12k a turn
                    + ["--tools", "Bash", "Read", "Write", "Edit"]
                    + (["--effort", effort] if effort else [])
                    + ["--output-format", "stream-json", "--verbose"],
                    cwd=self.wt,
                    stdin=subprocess.DEVNULL,
                    # a step lasts minutes: a 1h cache write costs 2x, 5m 1.25x
                    env=os.environ
                    | {
                        "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
                        "CLAUDE_CODE_PROMPT_CACHE_TTL": "5m",
                    },
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    timeout=self.hours * 3600,
                )
            with log.open() as f:
                f.seek(start)
                events = f.read()
            wait = limit_reset(events)
            if wait is None:
                break
            self.progress(f"{step}: usage limit, waiting {wait / 60:.0f} min")
            time.sleep(wait)
        self.tokens(step, model, events)

    def tokens(self, step: str, model: str, events: str) -> None:
        for line in events.splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or r.get("type") != "result":
                continue
            u = r.get("usage", {})
            row = [
                step,
                model,
                u.get("input_tokens", 0),
                u.get("cache_read_input_tokens", 0),
                u.get("cache_creation_input_tokens", 0),
                u.get("output_tokens", 0),
                f"{r.get('total_cost_usd', 0):.2f}",
            ]
            with (self.scratch / "tokens.tsv").open("a") as f:
                f.write("\t".join(map(str, row)) + "\n")

    def check(self) -> list[str]:
        done = subprocess.run(
            ["uv", "run", "algo-coach", "module", "check"]
            + ["--content", str(self.wt / "modules"), self.module],
            cwd=self.engine,
            capture_output=True,
            text=True,
        )
        out = done.stdout + done.stderr
        if not re.search(r"^0 errors", out, re.M):
            return [line for line in out.splitlines() if not line.startswith("warning")][-40:]
        return []

    def clean(self, stage: int, step: str) -> None:
        """The check passes after a step, or one fix pass makes it pass."""
        errors = self.check()
        if not errors:
            return
        self.session(
            "fix-check",
            self.fixer(stage),
            f"{step} check",
            given=self.given("fix-check", stage),
            stage=stage,
            errors="\n".join(errors),
        )
        if errors := self.check():
            raise Failed(f"stage {stage} {step}: check: {errors[-1]}")


def run(job: Job, last: int = 3) -> bool:
    """Whether the subtopic is written, which a stop after `last` leaves not."""
    for stage in range(1, last + 1):
        if not job.state().get(f"s{stage}-end"):
            run_stage(job, stage)
    if last < 3:
        return False
    if not job.state().get("digest"):
        digest = job.wt / "modules" / job.module / "review"
        digest /= f"{job.topic}-{job.sub}-L{job.level}.md"
        given = job.given("digest", 3, [job.scratch / "decisions.md", job.scratch / "progress.md"])
        job.session("digest", job.models["digest"], "digest", given=given, digest=digest)
        job.mark("digest")
        job.progress("digest written")
    return True


def run_stage(job: Job, n: int) -> None:
    folder = job.scratch / f"stage{n}"
    folder.mkdir(exist_ok=True)
    if not job.state().get(f"s{n}-write"):
        job.progress(f"stage {n} start")
        job.session(
            f"write-{n}", job.models["writer"], f"stage {n} write", given=job.given("write", n)
        )
        job.clean(n, "write")
        job.mark(f"s{n}-write")
        job.progress(f"stage {n} written, check 0 errors")
    solver = folder / "solver"
    if n == 3 and not job.state().get("s3-solver"):
        solve(job, solver)
        job.mark("s3-solver")
    fulls, clean_full = 0, False
    for r in range(1, MAX_ROUNDS + 1):
        full = fulls < MAX_FULL and not clean_full
        report = folder / f"review-{r}.md"
        key = f"s{n}-r{r}"
        counts = job.state().get(f"{key}-review")
        if counts is None:
            counts = review(job, n, r, full, solver)
        wrong = counts[0]
        if full:
            fulls += 1
            clean_full = wrong == 0
        if sum(counts) == 0:
            break
        if not job.state().get(f"{key}-fix"):
            fix(job, n, r, report)
        # a diff review with nothing wrong ends the stage after its fix
        if not full and wrong == 0:
            break
    else:
        raise Failed(f"stage {n}: {MAX_ROUNDS} rounds and still a WRONG finding")
    job.mark(f"s{n}-end")
    job.progress(f"stage {n} ends")


def review(job: Job, n: int, r: int, full: bool, solver: Path) -> list[int]:
    folder = job.scratch / f"stage{n}"
    report = folder / f"review-{r}.md"
    shown = [job.scratch / "decisions.md"]
    if full:
        scope = "Review the whole layer: " + LAYERS[n].format(**job.fields()) + "."
        if n == 3 and r == 1:
            shown.append(solver / "findings.md")
            scope += (
                f" The solver's findings in {solver}/findings.md are findings to"
                " verify: judge each as the solver skill's step 5 gives."
            )
    else:
        shown.append(folder / f"fix-{r - 1}.diff")
        scope = (
            f"Review only the last fix pass, the diff {folder}/fix-{r - 1}.diff. Read"
            " each file it changed as it stands now, and check the changed lines"
            " against the layer above and the rules. A line the diff leaves"
            " unchanged is out of scope unless the change makes it wrong."
        )
    kind = "full" if full else "diff"
    given = job.given("review", n, shown)
    # a session stopped part way may have left half a report
    report.unlink(missing_ok=True)
    step = f"stage {n} review {r} ({kind})"
    job.session(
        "review", job.models["reviewer"], step, given=given, stage=n, scope=scope, report=report
    )
    first = report.read_text().splitlines()[0] if report.exists() else ""
    if not (m := COUNTS.match(first)):
        raise Failed(f"stage {n} review {r}: no COUNTS line")
    counts = list(map(int, m.groups()))
    if job.shadow:
        shadow.reviews(job, n, r, kind, given, scope, report)
    job.mark(f"s{n}-r{r}-review", counts)
    job.progress(f"{step}: {counts[0]} WRONG, {counts[1]} DEFECT, {counts[2]} STYLE")
    return counts


def fix(job: Job, n: int, r: int, report: Path) -> None:
    key = f"s{n}-r{r}"
    # the index holds the layer before the fix: the diff is the fix. A fix
    # stopped part way keeps the index it staged.
    if not job.state().get(f"{key}-staged"):
        subprocess.run(["git", "add", "-A", "modules"], cwd=job.wt, check=True)
        job.mark(f"{key}-staged")
    job.session(
        "fix",
        job.fixer(n),
        f"stage {n} fix {r}",
        given=job.given("fix", n, [report, job.scratch / "decisions.md"]),
        stage=n,
        report=report,
    )
    job.clean(n, f"fix {r}")
    diff = subprocess.run(
        ["git", "diff", "--", "modules"], cwd=job.wt, capture_output=True, text=True
    ).stdout
    (job.scratch / f"stage{n}" / f"fix-{r}.diff").write_text(diff)
    job.mark(f"{key}-fix")
    job.progress(f"stage {n} fix {r}: {diff.count(chr(10))} diff lines, check 0 errors")


def solve(job: Job, out: Path) -> None:
    script = [".claude/skills/solver/solve.py"]
    module = job.wt / "modules" / job.module
    subprocess.run(
        ["uv", "run", "python", *script, "extract", str(module), str(out), job.sub],
        cwd=job.engine,
        check=True,
        capture_output=True,
    )
    if json.loads((out / "questions.json").read_text()):
        job.session("solve", job.models["solver"], "stage 3 solve", out=out)
    else:
        (out / "replies.json").write_text("[]")
    job.session("form", job.models["form"], "stage 3 form", out=out)
    subprocess.run(
        ["uv", "run", "python", *script, "score", str(out)],
        cwd=job.engine,
        check=True,
        capture_output=True,
    )
    job.progress("stage 3 solver: findings.md written")


def limit_reset(events: str) -> float | None:
    """Seconds until the usage limit resets, if the session ended on it."""
    if '"api_error":"usage_limit_reached"' not in events:
        return None
    m = re.search(r"resets (\d{1,2})(?::(\d\d))?\s*(am|pm)", events)
    if not m:
        return 15 * 60
    hour = int(m[1]) % 12 + (12 if m[3] == "pm" else 0)
    now = datetime.datetime.now()
    at = now.replace(hour=hour, minute=int(m[2] or 0), second=0, microsecond=0)
    if at <= now:
        at += datetime.timedelta(days=1)
    # a few minutes past the reset, so the first call lands after it
    return (at - now).total_seconds() + 5 * 60
