import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from textwrap import fill

from algo_coach.claims import against, claimable, contested, readings_at, revisable, standing_claims
from algo_coach.classifier import request_hash
from algo_coach.cli.display import verdict
from algo_coach.cli.prompts import NONE, ask_choice, numbered
from algo_coach.cli.score import configurations, labels
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import load_problems
from algo_coach.schema import Attempt, Confidence, Problem, TechniqueClaim
from algo_coach.techniques import criterion

WIDTH = 100
LEVELS = list(Confidence)


def claim(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The drill loop's technique question, over attempts already in the log.

    With `--revise`, the same question over what the hand pass already
    answered.
    """
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in load_problems(root)}
    claims = log.claims()
    standing = standing_claims(claims)

    if args.revise:
        pool, readings, names = disputed(args, parser, claims, log, problems, standing)
    else:
        if args.named or args.disputed is not None:
            parser.exit(2, "claim: --model, --effort and --disputed need --revise\n")
        pool, readings, names = (
            claimable(
                log.attempts(),
                problems,
                standing,
                user_id=args.user,
                technique=args.technique,
                seed=args.seed,
            ),
            [],
            [],
        )
    if not pool:
        # "disputed" only where that is what emptied it: the revision pool is
        # every claim by default.
        left = "left to claim"
        if args.revise:
            left = "disputed" if args.disputed else "to revise"
        # Zero: an empty pool is a completed query, and nothing disputed is
        # what adjudication stops on. Misuse still exits 2.
        parser.exit(0, f"claim: nothing {left} for {args.user}\n")

    # Once, unlike the candidates: the levels are the same at every attempt.
    print(f"\nconfidence: {numbered(LEVELS)}")
    # `0` and `s` are the pair worth spelling out: one is a verdict about the
    # code, the other leaves the attempt unanswered.
    kept = "keeps the claim" if args.revise else "skips"
    print(f"keys: numbers to name, 0 for {NONE}, s skips, enter {kept}, a stops.")

    written = 0
    for index, attempt in enumerate(pool[: args.count], start=1):
        problem = problems[attempt.problem_id]
        print(f"\n{index}/{min(args.count, len(pool))}  {problem.title}")
        print(f"{verdict(attempt)}, {attempt.finished_at:%Y-%m-%d}")
        print(code_excerpt(attempt.code or "", args.lines))
        if args.revise:
            print(read_as(attempt, standing[attempt.id], readings, names))
        # Printed per attempt: the candidates are this problem's techniques.
        print(f"  {numbered(problem.techniques)}")

        # In the candidates' order, since that is what the numbers select.
        rules = [text for code in problem.techniques if (text := rule(code))]
        print(f"\n{'\n\n'.join(rules)}\n")

        answer = ask_choice(
            "techniques",
            problem.techniques,
            [],
            empty="keep" if args.revise else "skip",
            # Without `0`, a hand claim could only be overturned by deleting
            # it, which drops the attempt out of the eval set.
            none=NONE,
        )
        if answer is None or answer.rest:
            break
        if answer.picked is None:
            continue
        chosen = [problem.techniques[int(number) - 1] for number in answer.picked]

        # Empty leaves it unsaid rather than defaulting to the middle.
        level = ask_choice("confidence", LEVELS, [], empty="unsaid")
        if level is None:
            break
        log.append_claim(
            user_claim(
                attempt.id,
                chosen,
                # `0` came back as an empty list; the schema refuses an empty
                # claim that does not say it is one.
                declined=not chosen,
                confidence=LEVELS[int(level.picked[0]) - 1] if level.picked else None,
                informed_by=shown(attempt, readings),
            )
        )
        written += 1
        # After the append, since the techniques answer already landed.
        if level.rest:
            break

    print(f"\n{written} claim(s) written")


def disputed(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    claims: Sequence[TechniqueClaim],
    log: AttemptLog,
    problems: Mapping[str, Problem],
    standing: Mapping[str, TechniqueClaim],
) -> tuple[list[Attempt], list[Mapping[str, TechniqueClaim]], list[str]]:
    """The revision pool and what each named classifier read it as."""
    named = configurations(args, parser)
    pool = revisable(
        log.attempts(),
        problems,
        standing,
        user_id=args.user,
        technique=args.technique,
    )
    # What each attempt would be asked now: a reading of an older rulebook
    # answered a different question.
    asked = {
        attempt.id: request_hash(problems[attempt.problem_id].techniques, attempt.code or "")
        for attempt in pool
    }
    readings = [readings_at(claims, configuration, asked) for configuration in named]
    pool = contested(
        pool,
        standing,
        readings,
        at_least=args.disputed if args.disputed is not None else 0,
    )
    return pool, readings, labels(named)


# The calls whose verdicts `read_as` showed. The pool only promises that one
# configuration disagreed, not that all answered.
def shown(attempt: Attempt, readings: Sequence[Mapping[str, TechniqueClaim]]) -> list[str]:
    return [
        reading.call_id
        for stored in readings
        if (reading := stored.get(attempt.id)) is not None and reading.call_id is not None
    ]


def read_as(
    attempt: Attempt,
    claim: TechniqueClaim,
    readings: Sequence[Mapping[str, TechniqueClaim]],
    names: Sequence[str],
) -> str:
    """The standing claim and what each classifier read the same code as."""
    width = max(len(name) for name in ("you", *names)) + 1
    lines = [f"  {'you:'.ljust(width)} {' '.join(claim.techniques)}"]
    for name, stored in zip(names, readings, strict=True):
        reading = stored.get(attempt.id)
        if reading is not None:
            lines.append(f"  {(name + ':').ljust(width)} {' '.join(reading.techniques)}")
    lines.append(f"  {against(claim, readings)} of {len(names)} disagree")
    return "\n".join(lines)


def code_excerpt(code: str, limit: int) -> str:
    lines = code.splitlines()
    if len(lines) <= limit:
        return code
    return "\n".join([*lines[:limit], f"... {len(lines) - limit} more lines"])


def rule(code: str) -> str:
    """One candidate's criterion, verbatim from the vocabulary and wrapped for
    a terminal. Only the wrapping is this reader's."""
    return "\n".join(
        fill(line, width=WIDTH, initial_indent="  ", subsequent_indent="      ")
        for line in criterion(code)
    )
