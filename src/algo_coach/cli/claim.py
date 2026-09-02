import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from textwrap import fill

from algo_coach.claims import against, claimable, contested, readings_at, revisable
from algo_coach.classifier import request_hash
from algo_coach.cli.display import verdict
from algo_coach.cli.prompts import NONE, ask_choice, numbered
from algo_coach.cli.score import configurations, labels
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Confidence, Problem, TechniqueClaim
from algo_coach.techniques import criterion, standing_claims

WIDTH = 100
LEVELS = list(Confidence)


def claim(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The drill loop's technique question, pointed at attempts already in the
    log. No sitting to be present at — the evidence is the code, which stays.

    With `--revise`, the same question over what the hand pass already
    answered: a claim is open to revision, and a reading that disagrees is the
    only place a mislabelled one surfaces.
    """
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
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
        # "disputed" only where that is what emptied it. The revision pool is
        # every claim by default, so an empty one means none were made.
        left = "left to claim"
        if args.revise:
            left = "disputed" if args.disputed else "to revise"
        # Zero, because an empty pool is a completed query rather than a
        # fault. Nothing disputed is what adjudication stops on, so the status
        # would contradict the message it prints. Misuse still exits 2.
        parser.exit(0, f"claim: nothing {left} for {args.user}\n")

    # Once, unlike the candidates: the levels are the same at every attempt.
    print(f"\nconfidence: {numbered(LEVELS)}")
    # What each answer does, said before the first prompt rather than only in
    # the retry hint. `0` and `s` are the pair worth spelling out: one is a
    # verdict about the code, the other leaves the attempt unanswered.
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
            # Naming none of them is a verdict about the code, and the
            # classifier can already record it. Without it here, a hand claim
            # could only be overturned by deleting it, which drops the attempt
            # out of the eval set entirely.
            none=NONE,
        )
        if answer is None or answer.rest:
            break
        if answer.picked is None:
            continue
        chosen = [problem.techniques[int(number) - 1] for number in answer.picked]

        # Empty leaves it unsaid rather than defaulting to the middle: a level
        # nobody gave is not a level, and the eval reads the absence.
        level = ask_choice("confidence", LEVELS, [], empty="unsaid")
        if level is None:
            break
        log.append_claim(
            user_claim(
                attempt.id,
                chosen,
                # `0` came back as an empty list, which no other reply gives.
                # Stated rather than inferred: the schema refuses an empty
                # claim that does not say it is one.
                declined=not chosen,
                confidence=LEVELS[int(level.picked[0]) - 1] if level.picked else None,
                informed_by=shown(attempt, readings),
            )
        )
        written += 1
        # `a` at either prompt stops outright, as the drill loop's do — but
        # after the append here, since the techniques answer already landed.
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
    """The revision pool and what each named classifier read it as.

    Named configurations rather than every one in the log: which readings are
    worth seeing beside a claim is the reader's question, and a column per
    configuration ever run would answer it for them.
    """
    named = configurations(args, parser)
    pool = revisable(
        log.attempts(),
        problems,
        standing,
        user_id=args.user,
        technique=args.technique,
    )
    # What each attempt would be asked now. A reading of an older rulebook
    # answered a different question, so showing it beside a claim would put a
    # disagreement with text nobody sends any more in front of the reader.
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


def shown(attempt: Attempt, readings: Sequence[Mapping[str, TechniqueClaim]]) -> list[str]:
    """The calls whose verdicts `read_as` put in front of the reader.

    A named configuration that never read this attempt showed nothing, so it
    informed nothing — the pool only promises that one of them disagreed, not
    that all of them answered.
    """
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
    """The standing claim and what each classifier read the same code as.

    Shown before the answer, which is the reader's choice and has a cost: a
    claim made with the readings in view is no longer independent of them, and
    the agreement it is later scored on measures rather less than it did.
    """
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
    """One candidate's criterion, in the classifier's own words and wrapped for
    a terminal. The words are the vocabulary's; only the wrapping is this
    reader's, so what the two annotators are asked cannot drift apart."""
    return "\n".join(
        fill(line, width=WIDTH, initial_indent="  ", subsequent_indent="      ")
        for line in criterion(code)
    )
