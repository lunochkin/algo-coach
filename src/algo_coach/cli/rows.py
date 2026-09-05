"""Flags that belong together in the order given: one opens a row, and the
settings after it fill its slots."""

import argparse
from collections.abc import Sequence


class Rows(argparse.Action):
    """`opener` and its settings alternately, into one ordered list. Separate
    `append` destinations would lose which setting followed which opener.

    `fills` are the flags after the opener, in the order their slots take. A
    setting before any opener begins a row with `opens_by_default`, or is
    refused where there is none: a value meant for one row would otherwise land
    on whichever the list happens to open with.
    """

    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        *,
        opener: str,
        fills: Sequence[str],
        opens_by_default: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(option_strings, dest, **kwargs)  # type: ignore[arg-type]
        self.opener = opener
        self.slots = {flag: index for index, flag in enumerate(fills, start=1)}
        self.opens_by_default = opens_by_default

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        command = parser.prog.split()[-1]
        rows: list[list[str]] = getattr(namespace, self.dest, None) or []
        blank = [""] * len(self.slots)
        if option_string == self.opener:
            rows.append([str(value), *blank])
        else:
            if not rows:
                if self.opens_by_default is None:
                    parser.exit(2, f"{command}: name a {self.opener} before {option_string}\n")
                rows.append([self.opens_by_default, *blank])
            slot = self.slots[str(option_string)]
            if rows[-1][slot]:
                parser.exit(2, f"{command}: two {option_string} for one {self.opener}\n")
            rows[-1][slot] = str(value)
        setattr(namespace, self.dest, rows)


__all__ = ["Rows"]
