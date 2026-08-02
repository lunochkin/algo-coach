import argparse
import json
import os
import sys
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from algo_coach.board import ProblemRow, TechniqueRow, candidates, per_technique, ungrouped
from algo_coach.ingest import ingest_attempts, ingest_problems
from algo_coach.log import AttemptLog, appeared, latest_by_attempt
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    ClaimSource,
    FailureMode,
    Problem,
    SelfLabel,
    TechniqueClaim,
)

DATA_ROOT = Path("data")


class BadLine(Exception):
    """Not JSON at all: corrupt transport, not an invalid record. Ingest never
    sees it, so it cannot come back as a rejection."""


def _read_jsonl(source: str) -> Iterator[dict]:
    """One record per line, so a half-written file is still half-ingestible."""
    lines = sys.stdin if source == "-" else Path(source).read_text().splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise BadLine(f"line {number}: {exc.msg}") from exc


def _user_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="identity to stamp on ingested records; stands in for authentication",
    )


def _push(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    records = _read_jsonl(args.source)
    try:
        if args.kind == "attempts":
            result = ingest_attempts(
                records,
                user_id=args.user,
                log=AttemptLog(DATA_ROOT),
                problems=ProblemStore(DATA_ROOT),
            )
        else:
            result = ingest_problems(records, user_id=args.user, store=ProblemStore(DATA_ROOT))
    except BadLine as exc:
        # Records before it are stored; re-pushing the fixed file is a no-op
        # on those, so resuming means running the command again.
        parser.exit(2, f"push: {exc}\n")

    print(result.model_dump_json(indent=2))
    if result.rejected:
        parser.exit(1)


def _board(args: argparse.Namespace) -> None:
    log = AttemptLog(DATA_ROOT)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    # Every problem, not the user's: an attempt resolves through the id it was
    # ingested with, and a narrower mapping would raise on a legitimate one.
    problems = {problem.id: problem for problem in ProblemStore(DATA_ROOT).all()}
    claims = latest_by_attempt(log.claims())
    labels = latest_by_attempt(log.self_labels())
    rows = per_technique(attempts, problems, claims, labels)
    if args.stale:
        rows.sort(key=lambda row: row.last_attempt_at)
    missed = len(ungrouped(attempts, problems, claims))

    if args.json:
        payload = {"rows": [row.model_dump(mode="json") for row in rows], "ungrouped": missed}
        print(json.dumps(payload, indent=2))
        return

    if not rows:
        print(f"no attempts for {args.user}")
        return

    print(_render(rows, datetime.now(UTC)))
    if missed:
        noun = "attempt" if missed == 1 else "attempts"
        print(f"\n{missed} {noun} grouped nowhere — no technique resolved")


def _drill(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Pick, point, hand over, then wait for the push and read what it added.
    Asking about each attempt is the step still missing."""
    log = AttemptLog(DATA_ROOT)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    stored = ProblemStore(DATA_ROOT).all()
    now = datetime.now(UTC)

    # Only the first prompt needs the board. Named outright, a technique with
    # no history is still drillable — which is the case a new store is in.
    technique = args.technique or _pick_technique(args, parser, log, attempts, stored, now)

    offers = candidates(technique, stored, attempts)
    if not offers:
        parser.exit(1, f"drill: no problem carries {technique}\n")
    problem = _choose(
        "problem",
        [(row, _problem_choice(row, now)) for row in offers[: args.limit]],
        parser,
    )

    known = {attempt.id for attempt in attempts if attempt.problem_id == problem.problem.id}

    print(f"\n{problem.problem.title} — {technique}")
    if problem.problem.url:
        print(problem.problem.url)
    print(_problem_history(problem, now))

    fresh = _await_push(problem.problem.id, known, args.user)
    if not fresh:
        print("nothing recorded")
        return
    claims, labels = _record_answers(fresh, problem.problem, technique, log)
    print(f"\nrecorded {claims} claim(s), {labels} label(s) over {len(fresh)} attempt(s)")


def _pick_technique(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    log: AttemptLog,
    attempts: list[Attempt],
    stored: list[Problem],
    now: datetime,
) -> str:
    """The board, stalest first. Without one there is nothing to choose from,
    so an empty log ends the drill here rather than at the problem step."""
    rows = per_technique(
        attempts,
        {problem.id: problem for problem in stored},
        latest_by_attempt(log.claims()),
        latest_by_attempt(log.self_labels()),
    )
    if not rows:
        parser.exit(1, f"drill: no attempts for {args.user}, name a technique to drill\n")
    rows.sort(key=lambda row: row.last_attempt_at)
    return _choose(
        "technique",
        [(row.technique, _technique_choice(row, now)) for row in rows[: args.limit]],
        parser,
    )


def _await_push(problem_id: str, known: set[str], user_id: str) -> list[Attempt]:
    """Waits on the user rather than a client: the engine calls nothing, and
    re-reading its own log answers exactly what a push added.

    An empty log after a push is not an error — the export may not have run
    yet — so it asks again until something appears or the drill is ended.
    """
    while True:
        print("\nSolve it there and push. Enter when pushed, or q to end.")
        try:
            if input("pushed? ").strip().lower() in {"q", "quit"}:
                return []
        except EOFError:
            print()
            return []

        attempts = [
            attempt for attempt in AttemptLog(DATA_ROOT).attempts() if attempt.user_id == user_id
        ]
        fresh = appeared(attempts, problem_id=problem_id, known=known)
        if fresh:
            return fresh
        print("nothing new in the log for this problem")


def _record_answers(
    fresh: list[Attempt], problem: Problem, technique: str, log: AttemptLog
) -> tuple[int, int]:
    """A claim and a self-label per attempt, both defaulted so a long sitting
    stays affordable.

    The drilled technique seeds the claim — selection picked the problem by its
    own tags, so it is always a legal one — and each answer becomes the next
    attempt's default. `a` accepts the defaults for everything remaining, `s`
    records nothing for that question.
    """
    options = sorted(set(problem.techniques) | {technique})
    modes = list(FailureMode)
    print(f"\n{len(fresh)} to record. Enter takes the default, a takes it for the rest, s skips.")
    print("  techniques  " + "   ".join(f"{i} {code}" for i, code in enumerate(options, 1)))
    print("  labels      " + "   ".join(f"{i} {mode}" for i, mode in enumerate(modes, 1)))

    claimed = [technique]
    labelled: FailureMode | None = None
    rest = False
    claims = labels = 0

    for index, attempt in enumerate(fresh, start=1):
        print(f"\n{index}/{len(fresh)}  {attempt.finished_at:%Y-%m-%d %H:%M}  {_verdict(attempt)}")
        if not rest:
            seeded = [str(options.index(code) + 1) for code in claimed]
            answer = _ask_choice("techniques", options, seeded)
            if answer is None:
                break
            if answer.picked is not None:
                claimed = [options[int(number) - 1] for number in answer.picked]
            elif not answer.rest:
                claimed = []

            # `a` at either prompt stops the questions outright, so it does not
            # cost a second keystroke on the attempt that ends them.
            rest = answer.rest
            if not rest:
                picked_label = _ask_choice(
                    "label", modes, [str(modes.index(labelled) + 1)] if labelled else []
                )
                if picked_label is None:
                    break
                rest = picked_label.rest
                if picked_label.picked is not None:
                    labelled = modes[int(picked_label.picked[0]) - 1]
                elif not picked_label.rest:
                    labelled = None

        if claimed:
            log.append_claim(
                TechniqueClaim(
                    id=uuid.uuid4().hex,
                    created_at=datetime.now(UTC),
                    attempt_id=attempt.id,
                    techniques=claimed,
                    source=ClaimSource.USER,
                )
            )
            claims += 1
        if labelled is not None:
            log.append_self_label(
                SelfLabel(
                    id=uuid.uuid4().hex,
                    created_at=datetime.now(UTC),
                    attempt_id=attempt.id,
                    mode=labelled,
                )
            )
            labels += 1
    return claims, labels


class _Answer(NamedTuple):
    picked: list[str] | None  # None when skipped or defaulted away
    rest: bool  # apply the defaults to every attempt still to come


def _ask_choice(what: str, options: list, default: list[str]) -> _Answer | None:
    """One prompt over a numbered list. None on EOF, which ends the recording
    with whatever already landed — the log is append-only either way."""
    shown = ",".join(default) if default else "skip"
    while True:
        try:
            answer = input(f"  {what} [{shown}]: ").strip().lower()
        except EOFError:
            print()
            return None
        if answer == "s":
            return _Answer(None, False)
        if answer in {"a", ""}:
            return _Answer(default or None, answer == "a")
        numbers = [part.strip() for part in answer.split(",") if part.strip()]
        if numbers and all(n.isdigit() and 1 <= int(n) <= len(options) for n in numbers):
            return _Answer(numbers, False)
        print(f"  pick numbers between 1 and {len(options)}, or a, or s")


def _verdict(attempt: Attempt) -> str:
    return attempt.source_status or ("solved" if attempt.solved else "unsolved")


def _technique_choice(row: TechniqueRow, now: datetime) -> str:
    solved = f"{row.solved_count}/{row.attempt_count}"
    return f"{row.technique:22} {solved:<9} {_age(row.last_attempt_at, now)}"


def _problem_choice(row: ProblemRow, now: datetime) -> str:
    solved = f"{row.solved_count}/{row.attempt_count}"
    return f"{row.problem.title[:38]:40} {solved:<7} {_age(row.last_attempt_at, now)}"


def _problem_history(row: ProblemRow, now: datetime) -> str:
    if row.last_attempt_at is None:
        return "never attempted"
    solved = f"{row.solved_count}/{row.attempt_count}"
    return f"last attempted {_age(row.last_attempt_at, now)}, solved {solved}"


def _age(when: datetime | None, now: datetime) -> str:
    if when is None:
        return "never"
    # Clamped: a submission stamped later today is not negatively old.
    days = max((now - when).days, 0)
    return f"{when:%Y-%m-%d} ({days}d)"


def _choose[T](what: str, options: list[tuple[T, str]], parser: argparse.ArgumentParser) -> T:
    """Numbered list, one line each, re-asked until it resolves. EOF ends the
    drill rather than picking for the user."""
    for index, (_, line) in enumerate(options, start=1):
        print(f"{index:3}  {line}")
    while True:
        try:
            answer = input(f"{what} [1-{len(options)}]: ").strip()
        except EOFError:
            parser.exit(2, f"\ndrill: no {what} chosen\n")
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1][0]
        print(f"pick a number between 1 and {len(options)}")


def _render(rows: list[TechniqueRow], now: datetime) -> str:
    """Fixed-width columns, in the order the caller settled on."""
    header = ("technique", "attempts", "solved", "last", "labels")
    body = [
        (
            row.technique,
            str(row.attempt_count),
            f"{row.solved_count}/{row.attempt_count}",
            f"{row.last_attempt_at:%Y-%m-%d} ({(now - row.last_attempt_at).days}d)",
            " ".join(f"{mode}:{count}" for mode, count in sorted(row.self_labels.items())),
        )
        for row in rows
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="algo-coach")
    sub = parser.add_subparsers(dest="command", required=True)

    push_parser = sub.add_parser("push", help="ingest pushed records from JSONL")
    push_parser.add_argument("kind", choices=["attempts", "problems"])
    push_parser.add_argument("source", help="path to a JSONL file, or - for stdin")
    _user_argument(push_parser)

    board_parser = sub.add_parser("board", help="per-technique standing, derived from the log")
    board_parser.add_argument("--json", action="store_true", help="emit rows instead of a table")
    board_parser.add_argument(
        "--stale", action="store_true", help="order by recency, least recently practised first"
    )
    _user_argument(board_parser)

    drill_parser = sub.add_parser("drill", help="pick a technique, then a problem for it")
    drill_parser.add_argument("--technique", help="skip the first prompt with a known code")
    drill_parser.add_argument(
        "--limit", type=int, default=10, help="how many choices to offer at each step"
    )
    _user_argument(drill_parser)

    args = parser.parse_args()
    if args.command == "board":
        _board(args)
    elif args.command == "drill":
        _drill(args, parser)
    else:
        _push(args, parser)


if __name__ == "__main__":
    main()
