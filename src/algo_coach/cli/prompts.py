import argparse
from typing import NamedTuple


class Answer(NamedTuple):
    picked: list[str] | None  # None when skipped or defaulted away
    rest: bool  # apply the defaults to every attempt still to come


def ask_choice(what: str, options: list, default: list[str]) -> Answer | None:
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
            return Answer(None, False)
        if answer in {"a", ""}:
            return Answer(default or None, answer == "a")
        numbers = [part.strip() for part in answer.split(",") if part.strip()]
        if numbers and all(n.isdigit() and 1 <= int(n) <= len(options) for n in numbers):
            return Answer(numbers, False)
        print(f"  pick numbers between 1 and {len(options)}, or a, or s")


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
