"""The board a run of several classifiers shows while it is running.

What it must get right is who a line belongs to and that nothing tears: two
configurations answer at once, and a wait arrives on a thread of its own.
"""

import os
import re
import threading

from algo_coach.calls import Retry
from algo_coach.claims import Configuration
from algo_coach.cli.status import BAR, Status


class Stream:
    """A stream that says whether it is a terminal, and keeps every write
    whole — which is what the board's one-write rule is about."""

    def __init__(self, terminal: bool = False):
        self.terminal = terminal
        self.writes: list[str] = []

    def isatty(self) -> bool:
        return self.terminal

    def write(self, text: str) -> int:
        self.writes.append(text)
        return len(text)

    def flush(self) -> None:
        pass

    @property
    def text(self) -> str:
        return "".join(self.writes)


LOW = Configuration(model="a-model", effort="low", pin="a-host", temperature=0.0)
HIGH = Configuration(model="a-model", effort="high", pin="a-host", temperature=0.0)
OTHER = Configuration(model="b-model", effort="low", pin="b-host", temperature=None)


def retry(**overrides) -> Retry:
    fields = {
        "status": 429,
        "model": "a-model",
        "pin": "a-host",
        "tries": 2,
        "of": 5,
        "pause": 15.0,
        "reason": "Rate limit exceeded",
    }
    return Retry(**{**fields, **overrides})


def test_a_row_per_configuration_in_the_order_named():
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH, OTHER])

    board.planned([2, 2, 2])

    rows = [line for line in stream.text.splitlines() if "a-model" in line or "b-model" in line]
    assert len(rows) == 3
    assert rows[0].index("low") > 0 and rows[1].index("high") > 0
    assert "b-model" in rows[2]


def test_two_configurations_on_one_deployment_are_told_apart():
    """The case the grouping exists for: same model, same endpoint, and only
    what they were asked at separates them."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH])

    board.planned([1, 1])

    rows = [line for line in stream.text.splitlines() if "a-model" in line]
    assert "low" in rows[0] and "high" not in rows[0]
    assert "high" in rows[1] and " low" not in rows[1]


def test_a_temperature_nobody_set_is_named_rather_than_blank():
    stream = Stream(terminal=True)
    board = Status(stream, [OTHER])

    board.planned([1])

    assert "default" in stream.text


def test_the_bar_fills_with_what_has_been_answered():
    stream = Stream(terminal=True)
    board = Status(stream, [LOW])
    board.planned([BAR])

    for _ in range(BAR // 2):
        board.answered(LOW)

    assert f"[{'#' * (BAR // 2)}{'-' * (BAR // 2)}]" in stream.writes[-1]


def test_a_failure_is_tallied_on_its_own_row():
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, OTHER])
    board.planned([2, 2])

    board.answered(LOW, failed=True)

    (row,) = [line for line in stream.writes[-1].splitlines() if "a-model" in line]
    assert "1 failed" in row
    assert "failed" not in [line for line in stream.writes[-1].splitlines() if "b-model" in line][0]


def test_a_wait_marks_every_row_the_deployment_holds():
    """Two configurations pinned to one endpoint are held by the same limit,
    so a cap is not one row's news."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH, OTHER])
    board.planned([2, 2, 2])

    board.waiting(retry())

    held = [line for line in stream.writes[-1].splitlines() if "held 15s" in line]
    assert len(held) == 2
    assert all("a-model" in line for line in held)


def test_an_answer_ends_the_wait_it_was_held_by():
    stream = Stream(terminal=True)
    board = Status(stream, [LOW])
    board.planned([2])
    board.waiting(retry())

    board.answered(LOW)

    assert "held 15s" not in stream.writes[-1]
    assert "1 held" in stream.writes[-1]


def test_a_terminal_redraws_in_place_rather_than_appending():
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH])
    board.planned([2, 2])

    board.answered(LOW)

    assert stream.writes[-1].startswith("\x1b[2A")
    assert "\x1b[2K" in stream.writes[-1]


def test_a_block_is_one_write_however_many_rows():
    """Split across writes, a wait arriving between them would land inside the
    block and scroll it."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH, OTHER])

    board.planned([2, 2, 2])

    assert len(stream.writes) == 1
    assert stream.writes[0].count("\n") == 3


def test_a_pipe_appends_plain_lines_with_no_escape_codes():
    """A file full of cursor movements is worse than no report at all."""
    stream = Stream(terminal=False)
    board = Status(stream, [LOW])
    board.planned([2])

    board.answered(LOW)
    board.answered(LOW)
    board.close()

    assert "\x1b" not in stream.text
    assert "a-model" in stream.text


def test_a_pipe_says_a_wait_as_its_own_line():
    """Nothing is being redrawn, so the wait is reported the way every other
    command reports one."""
    stream = Stream(terminal=False)
    board = Status(stream, [LOW])
    board.planned([2])

    board.waiting(retry())

    assert "! 429 a-model @ a-host" in stream.text


def test_a_run_that_will_call_nothing_draws_nothing():
    """`--stored` pays for nothing, and rows of 0/0 are not a report."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH])

    board.planned([0, 0])
    board.close()

    assert stream.writes == []


def test_a_row_that_asks_nothing_still_appears():
    """A configuration whose readings are all reused makes no call. Without a
    row it would be missing from a comparison it is part of."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, OTHER])

    board.planned([0, 3])

    assert "a-model" in stream.text
    assert "0/0" in stream.text


def test_a_wait_and_a_redraw_do_not_interleave():
    """Progress arrives on the consuming thread and a wait on whichever worker
    hit the cap. Every write must still be a whole block."""
    stream = Stream(terminal=True)
    board = Status(stream, [LOW, HIGH])
    board.planned([50, 50])

    def answering() -> None:
        for _ in range(50):
            board.answered(LOW)

    def holding() -> None:
        for _ in range(50):
            board.waiting(retry())

    threads = [threading.Thread(target=answering), threading.Thread(target=holding)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Every write after the first is a two-row block: the cursor jump, two
    # erased lines, and a trailing newline on each.
    for written in stream.writes[1:]:
        assert written.startswith("\x1b[2A")
        assert written.count("\n") == 2


def test_a_narrow_terminal_cuts_the_name_and_never_the_standing(monkeypatch):
    """The counts and the failure tally are what a row is for. The name is the
    part a reader already knows, so it is what gives way."""
    monkeypatch.setattr("shutil.get_terminal_size", lambda: os.terminal_size((44, 24)))
    stream = Stream(terminal=True)
    board = Status(stream, [LOW])
    board.planned([70])

    board.answered(LOW, failed=True)

    (row,) = [
        re.sub(r"\x1b\[[0-9]*[A-Za-z]", "", line)
        for line in stream.writes[-1].splitlines()
        if "/70" in line
    ]
    assert row.endswith("1 failed")
    assert "…" in row
    assert len(row) <= 43
