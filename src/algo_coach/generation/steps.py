"""What a run reports while one problem is being written.

Three calls and a mutation loop take minutes. A run reporting one line per
problem shows nothing until the problem has landed or been lost, so each stage
says what it is doing and what it left.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from algo_coach.schema import Call


class Step(BaseModel):
    """One stage of writing a problem, reported as it starts and as it ends."""

    index: int  # 1-based, over what the run asks for
    total: int
    name: str  # the stage: statement, reference, cases, inputs, mutants, round, timing
    detail: str = ""
    # what the stage paid for, where it made a call. Whole rather than by id:
    # the renderer reads the tokens and the wait, and the log is not loaded
    call: Call | None = None


@dataclass(frozen=True)
class Notes:
    """Where a stage's lines go, and which problem they belong to.

    Silent by default, so `write_one` and `harden` are callable without a
    reporter and a test needs none.
    """

    on_step: Callable[[Step], None] | None = None
    index: int = 1
    total: int = 1

    def __call__(self, name: str, detail: str = "", call: Call | None = None) -> None:
        if self.on_step is None:
            return
        self.on_step(Step(index=self.index, total=self.total, name=name, detail=detail, call=call))


SILENT = Notes()


__all__ = ["SILENT", "Notes", "Step"]
