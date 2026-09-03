"""One row per configuration while a run of several classifiers is going. The
only writer to the stream during a run: progress arrives on the consuming
thread and a wait on whichever worker hit the cap, so both are serialised."""

import shutil
import threading
from dataclasses import dataclass
from typing import TextIO

from algo_coach.calls import Configuration, Retry
from algo_coach.cli.display import held, sampled

# Cells in the bar, so one cell is ten per cent.
BAR = 10

# Updates a row prints when it cannot redraw: a run of minutes must not go
# silent, and a line per attempt is what the board replaced.
STEPS = 10


@dataclass
class Row:
    configuration: Configuration
    total: int = 0
    answered: int = 0
    failed: int = 0
    held: int = 0  # waits this row has been through
    holding: float = 0.0  # the wait in progress, cleared by the next answer
    shown: int = 0  # `answered` when this row last printed, on a pipe


@dataclass
class Widths:
    """Measured once. A row that wrapped would make `redraw`'s up-count wrong."""

    model: int = 0
    effort: int = 0
    temperature: int = 0
    pin: int = 0
    total: int = 0
    line: int = 0


class Status:
    def __init__(self, stream: TextIO, configurations: list[Configuration]) -> None:
        self.stream = stream
        self.rows = [Row(configuration) for configuration in configurations]
        self.lock = threading.Lock()
        # From what the stream is rather than from a flag: a pipe cannot act
        # on an escape sequence.
        self.terminal = getattr(stream, "isatty", lambda: False)()
        self.drawn = False
        self.widths = self.measure()

    def measure(self) -> Widths:
        if not self.rows:
            return Widths()
        one = [row.configuration for row in self.rows]
        widths = Widths(
            model=max(len(c.model) for c in one),
            effort=max(len(c.effort) for c in one),
            temperature=max(len(sampled(c.temperature)) for c in one),
            pin=max(len(c.pin) for c in one),
        )
        widths.line = shutil.get_terminal_size().columns - 1 if self.terminal else 0
        return widths

    def line(self, row: Row) -> str:
        widths = self.widths
        name = (
            f"{row.configuration.model:<{widths.model}}  "
            f"{row.configuration.effort:<{widths.effort}}  "
            f"{sampled(row.configuration.temperature):<{widths.temperature}}  "
            f"@ {row.configuration.pin:<{widths.pin}}"
        )
        filled = row.answered * BAR // row.total if row.total else 0
        bar = f"[{'#' * filled}{'-' * (BAR - filled)}]"
        counts = f"{row.answered:>{widths.total}}/{row.total}"
        standing = f"  {bar}  {counts}{self.tail(row)}"
        # The name gives way, never the standing: a cut line would otherwise
        # lose the counts and the failure tally first.
        room = self.widths.line - len(standing)
        if self.widths.line and len(name) > room:
            name = name[: max(room - 1, 0)] + "…"
        return name + standing

    def tail(self, row: Row) -> str:
        parts = []
        if row.holding:
            parts.append(f"held {row.holding:g}s")
        elif row.held:
            parts.append(f"{row.held} held")
        if row.failed:
            parts.append(f"{row.failed} failed")
        return "   " + ", ".join(parts) if parts else ""

    def planned(self, totals: list[int]) -> None:
        """What each row will pay for. A configuration whose readings are all
        reused asks nothing, so without this it would never appear."""
        with self.lock:
            for row, total in zip(self.rows, totals, strict=True):
                row.total = total
                row.shown = -1
            self.widths.total = max((len(str(total)) for total in totals), default=1)
            if any(totals):
                self.draw()

    def answered(self, configuration: Configuration, *, failed: bool = False) -> None:
        with self.lock:
            row = self.row(configuration)
            row.answered += 1
            row.failed += failed
            # The wait ended, whatever the answer was.
            row.holding = 0.0
            self.draw()

    def waiting(self, retry: Retry) -> None:
        """A cap, marked on every row the endpoint holds that will call. Shown
        rather than printed: a line of its own would scroll the block."""
        with self.lock:
            marked = False
            for row in self.rows:
                if not row.total:
                    continue
                if (row.configuration.model, row.configuration.pin) == (retry.model, retry.pin):
                    row.holding = retry.pause
                    row.held += 1
                    marked = True
            if self.terminal and marked:
                self.draw()
            elif not self.terminal:
                self.write(held(retry) + "\n")

    def close(self) -> None:
        """The finished board, left on screen: nothing after it says what the
        calls took."""
        with self.lock:
            if not any(row.total for row in self.rows):
                return
            if self.terminal:
                self.draw()
            else:
                for row in self.rows:
                    self.write(self.line(row) + "\n")

    def row(self, configuration: Configuration) -> Row:
        return next(row for row in self.rows if row.configuration == configuration)

    def draw(self) -> None:
        if self.terminal:
            self.redraw()
            return
        # Appended and thinned rather than redrawn: a pipe cannot move a
        # cursor.
        for row in self.rows:
            step = max(row.total // STEPS, 1)
            if row.answered and (row.answered - row.shown >= step or row.answered == row.total):
                self.write(self.line(row) + "\n")
                row.shown = row.answered

    # One write of the whole block: split, a wait arriving between the writes
    # would land inside it.
    def redraw(self) -> None:
        lines = [self.line(row)[: self.widths.line] for row in self.rows]
        up = f"\x1b[{len(lines)}A" if self.drawn else ""
        # Erased before written, or a shorter row leaves the tail of the
        # longer one it replaced.
        self.write(up + "".join(f"\x1b[2K{line}\n" for line in lines))
        self.drawn = True

    def write(self, text: str) -> None:
        self.stream.write(text)
        self.stream.flush()
