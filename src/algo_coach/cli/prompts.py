import argparse
from typing import NamedTuple


class Answer(NamedTuple):
    picked: list[str] | None  # None when skipped or defaulted away
    rest: bool  # apply the defaults to every attempt still to come


def ask_choice(
    what: str, options: list, default: list[str], *, empty: str = "skip", none: str | None = None
) -> Answer | None:
    """One prompt over a numbered list. None on EOF, which ends the recording
    with whatever already landed — the log is append-only either way.

    `empty` names what an empty answer does where "skip" would mislead: over an
    attempt already claimed, writing nothing keeps the claim rather than
    leaving it unanswered.

    `none` opens `0`, for the question where naming nothing is an answer rather
    than a decline. A match asserts a pair, so a problem exercising none of a
    card's forms is a verdict on every one of them. It comes back as an empty
    list, which no other reply gives. A skip is `None`, and the two must not be
    read as one, since only one of them is evidence. Closed unless a caller
    names it: an empty claim would be indistinguishable from a stated one, and
    a skipped answer would read as an answer given.
    """
    shown = ",".join(default) if default else empty
    while True:
        try:
            answer = input(f"  {what} [{shown}]: ").strip().lower()
        except EOFError:
            print()
            return None
        if answer == "s":
            return Answer(None, False)
        if answer in {"a", ""}:
            return Answer(default or None, answer == "a")
        if none is not None and answer == "0":
            return Answer([], False)
        numbers = [part.strip() for part in answer.split(",") if part.strip()]
        if numbers and all(n.isdigit() and 1 <= int(n) <= len(options) for n in numbers):
            return Answer(numbers, False)
        zero = f", 0 for {none}" if none is not None else ""
        print(f"  pick numbers between 1 and {len(options)}{zero}, or a, or s")


def choose[T](what: str, options: list[tuple[T, str]], parser: argparse.ArgumentParser) -> T:
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


def numbered(items: list) -> str:
    """The candidates on one line, as the prompt numbers them."""
    return "   ".join(f"{index} {item}" for index, item in enumerate(items, start=1))
