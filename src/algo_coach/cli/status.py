"""What a run of several classifiers shows while it is running.

One row per configuration rather than a line per attempt. Several
configurations answer at once, and a line in that stream cannot say which
produced it without carrying the whole configuration on every one of them.

The only thing that writes to the stream while a run is going. Progress
arrives on the consuming thread and a wait arrives on whichever worker hit the
cap, so both are serialised here. A warning written beside a block being
redrawn would scroll the block and leave the cursor arithmetic wrong.
"""

import shutil
import threading
from dataclasses import dataclass
from typing import TextIO

from algo_coach.calls import Retry
from algo_coach.claims import Configuration
from algo_coach.cli.display import held, sampled

# Cells in the bar. Ten, so a cell is a readable ten per cent rather than a
# resolution nobody acts on.
BAR = 10

# Updates a row prints when nobody is watching it redraw. A run of minutes must
# not go silent, and a line per attempt is what the board replaced.
STEPS = 10


@dataclass
class Row:
    """One configuration's standing. Counted here rather than read from the
    run, since each answer reaches the board exactly once."""

    configuration: Configuration
    total: int = 0
    answered: int = 0
    failed: int = 0
    held: int = 0  # waits this row has been through
    holding: float = 0.0  # the wait in progress, cleared by the next answer
    shown: int = 0  # `answered` when this row last printed, on a pipe


@dataclass
class Widths:
    """Column widths, measured once. A row that wrapped would make the
    up-count wrong, which is the one failure that corrupts the display."""

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
        # Chosen once, from what the stream is rather than from a flag. A pipe
        # cannot act on an escape sequence, and a file full of them is worse
        # than no report at all.
        self.terminal = getattr(stream, "isatty", lambda: False)()
        self.drawn = False
        self.widths = self.measure()

    def measure(self) -> Widths:
        """Every field of every configuration is shown, so two that differ only
        in effort are told apart. The full identity costs width on a run where
        nothing collides, and reads the same in a pasted fragment as on screen.
        """
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
        # The name gives way, never the standing. A narrow terminal that cut
        # the line would take the counts and the failure tally first, which are
        # what the row is for — the name is the part a reader already knows.
        room = self.widths.line - len(standing)
        if self.widths.line and len(name) > room:
            name = name[: max(room - 1, 0)] + "…"
        return name + standing

    def tail(self, row: Row) -> str:
        """What is worth saying beside the count, in the order it matters: a
        wait happening now, then what the row has been through."""
        parts = []
        if row.holding:
            parts.append(f"held {row.holding:g}s")
        elif row.held:
            parts.append(f"{row.held} held")
        if row.failed:
            parts.append(f"{row.failed} failed")
        return "   " + ", ".join(parts) if parts else ""

    def planned(self, totals: list[int]) -> None:
        """What each row will pay for, before the first call.

        Totals are known only once every configuration has selected, and a
        configuration whose readings are all reused asks nothing — without this
        it would never appear, having no answer to report.
        """
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
        """A cap, marked on every row the deployment holds.

        Two configurations pinned to one endpoint are held by the same limit,
        so the mark belongs on both — but only on the ones that will call. A
        row asking nothing is answered from the log and never approaches the
        cap, so marking it would report a wait it is not in.

        The wait is shown rather than printed: a line of its own would scroll
        the block being redrawn.
        """
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
        """The finished board, left on screen. It is the run's cost, and the
        report that follows says nothing about what each call took."""
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
        # Appended rather than redrawn, and thinned: a pipe cannot move a
        # cursor, and a line per answer is the stream the board replaced.
        for row in self.rows:
            step = max(row.total // STEPS, 1)
            if row.answered and (row.answered - row.shown >= step or row.answered == row.total):
                self.write(self.line(row) + "\n")
                row.shown = row.answered

    def redraw(self) -> None:
        """One write of the whole block. Split across writes, a wait arriving
        between them would land inside it."""
        lines = [self.line(row)[: self.widths.line] for row in self.rows]
        up = f"\x1b[{len(lines)}A" if self.drawn else ""
        # Each line is erased before it is written, or a shorter row leaves the
        # tail of the longer one it replaced.
        self.write(up + "".join(f"\x1b[2K{line}\n" for line in lines))
        self.drawn = True

    def write(self, text: str) -> None:
        self.stream.write(text)
        self.stream.flush()
