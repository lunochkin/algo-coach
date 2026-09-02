from typing import NamedTuple


class Answer(NamedTuple):
    picked: list[str] | None  # None when skipped or defaulted away
    rest: bool  # apply the defaults to every attempt still to come


# What `0` answers. Worded once: the prompt, the loops and the retry hint
# all show it.
NONE = "none of these"


def ask_choice(
    what: str, options: list, default: list[str], *, empty: str = "skip", none: str | None = None
) -> Answer | None:
    """One prompt over a numbered list. `None` on EOF or a skip.

    `empty` names what an empty answer does. `none` opens `0`, which comes back
    as an empty list — a stated verdict, and no other reply gives one.
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


def numbered(items: list) -> str:
    return "   ".join(f"{index} {item}" for index, item in enumerate(items, start=1))
