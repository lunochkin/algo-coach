import argparse
import random
from pathlib import Path

from algo_coach.cli.display import verdict
from algo_coach.cli.prompts import ask_choice, numbered
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem


def claim(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The drill loop's technique question, pointed at attempts already in the
    log. No drill, no push — the evidence is the code, which is still there.

    Only attempts a claim would decide something about: unclaimed, carrying
    their code, on a problem whose tags leave a choice to make.
    """
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    claimed = latest_by_attempt(log.claims())
    pool = [
        attempt
        for attempt in log.attempts()
        if attempt.user_id == args.user
        and attempt.id not in claimed
        and attempt.code
        and decides_something(problems.get(attempt.problem_id), args.technique)
    ]
    if not pool:
        parser.exit(1, f"claim: nothing left to claim for {args.user}\n")

    # Shuffled rather than ordered, so a sample is not all of one era; seeded,
    # so a sample is described by its seed rather than by what it held.
    random.Random(args.seed).shuffle(pool)
    written = 0
    for index, attempt in enumerate(pool[: args.count], start=1):
        problem = problems[attempt.problem_id]
        print(f"\n{index}/{min(args.count, len(pool))}  {problem.title}")
        print(f"{verdict(attempt)}, {attempt.finished_at:%Y-%m-%d}")
        print(code_excerpt(attempt.code or "", args.lines))
        # Printed per attempt: the candidates are this problem's tags.
        print(f"  {numbered(problem.techniques)}")
        answer = ask_choice("techniques", problem.techniques, [])
        if answer is None or answer.rest:
            break
        if answer.picked is None:
            continue
        chosen = [problem.techniques[int(number) - 1] for number in answer.picked]
        log.append_claim(user_claim(attempt.id, chosen))
        written += 1

    print(f"\n{written} claim(s) written")


def decides_something(problem: Problem | None, technique: str | None) -> bool:
    """A single-tag problem needs no claim — the fallback already answers it,
    and a claim there would assert what nothing disputes."""
    if problem is None or len(problem.techniques) < 2:
        return False
    return technique is None or technique in problem.techniques


def code_excerpt(code: str, limit: int) -> str:
    lines = code.splitlines()
    if len(lines) <= limit:
        return code
    return "\n".join([*lines[:limit], f"... {len(lines) - limit} more lines"])
