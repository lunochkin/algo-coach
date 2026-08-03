import argparse
import uuid
from datetime import UTC, datetime
from pathlib import Path

from algo_coach.board import candidates, per_technique
from algo_coach.cli.display import problem_choice, problem_history, technique_choice, verdict
from algo_coach.cli.prompts import ask_choice, choose, numbered
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


def drill(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Pick, point, hand over, then wait for the push and read what it added."""
    log = AttemptLog(root)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    stored = ProblemStore(root).all()
    now = datetime.now(UTC)

    # Only the first prompt needs the board. Named outright, a technique with
    # no history is still drillable — which is the case a new store is in.
    technique = args.technique or pick_technique(args, parser, log, attempts, stored, now)

    offers = candidates(technique, stored, attempts)
    if not offers:
        parser.exit(1, f"drill: no problem carries {technique}\n")
    problem = choose(
        "problem",
        [(row, problem_choice(row, now)) for row in offers[: args.limit]],
        parser,
    )

    known = {attempt.id for attempt in attempts if attempt.problem_id == problem.problem.id}

    print(f"\n{problem.problem.title} — {technique}")
    if problem.problem.url:
        print(problem.problem.url)
    print(problem_history(problem, now))

    fresh = await_push(problem.problem.id, known, args.user, root)
    if not fresh:
        print("nothing recorded")
        return
    claims, labels = record_answers(fresh, problem.problem, technique, log)
    print(f"\nrecorded {claims} claim(s), {labels} label(s) over {len(fresh)} attempt(s)")


def pick_technique(
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
    return choose(
        "technique",
        [(row.technique, technique_choice(row, now)) for row in rows[: args.limit]],
        parser,
    )


def await_push(problem_id: str, known: set[str], user_id: str, root: Path) -> list[Attempt]:
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
            attempt for attempt in AttemptLog(root).attempts() if attempt.user_id == user_id
        ]
        fresh = appeared(attempts, problem_id=problem_id, known=known)
        if fresh:
            return fresh
        print("nothing new in the log for this problem")


def record_answers(
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
    print(f"  techniques  {numbered(options)}")
    print(f"  labels      {numbered(modes)}")

    claimed = [technique]
    labelled: FailureMode | None = None
    rest = False
    claims = labels = 0

    for index, attempt in enumerate(fresh, start=1):
        print(f"\n{index}/{len(fresh)}  {attempt.finished_at:%Y-%m-%d %H:%M}  {verdict(attempt)}")
        if not rest:
            seeded = [str(options.index(code) + 1) for code in claimed]
            answer = ask_choice("techniques", options, seeded)
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
                picked_label = ask_choice(
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
