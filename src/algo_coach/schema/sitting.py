"""One session on one problem, timed or not.

Revised while the sitting runs and kept after it ends. `log.md` gives why the
pauses are intervals rather than a total.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Pause(BaseModel):
    model_config = ConfigDict(frozen=True)

    at: datetime
    until: datetime | None = None  # absent while the sitting is paused

    @model_validator(mode="after")
    def _ends_after_it_starts(self) -> Pause:
        if self.until is not None and self.until < self.at:
            raise ValueError("a pause ends no earlier than it starts")
        return self


class Sitting(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    user_id: str = Field(min_length=1)
    problem_id: str = Field(min_length=1)
    started_at: datetime
    # absent while the clock has not run, and on a sitting it never ran on
    clock_started_at: datetime | None = None
    ended_at: datetime | None = None  # absent while the sitting runs
    # when the loop last acted on the sitting. Absent on a sitting stored
    # before the field, where the start stands in
    last_active_at: datetime | None = None
    pauses: list[Pause] = Field(default_factory=list[Pause])

    @property
    def paused(self) -> bool:
        return bool(self.pauses) and self.pauses[-1].until is None

    def elapsed(self, now: datetime) -> float | None:
        """Seconds the clock ran, every pause excluded. None on an untimed
        sitting."""
        if self.clock_started_at is None:
            return None
        end = self.ended_at or now
        paused = sum(((one.until or now) - one.at).total_seconds() for one in self.pauses)
        return (end - self.clock_started_at).total_seconds() - paused

    @model_validator(mode="after")
    def _the_intervals_hold(self) -> Sitting:
        """Rejects an elapsed time that would move with the moment it is read:
        a pause outside the clock's run, two that overlap, or one left open."""
        if self.clock_started_at is None:
            if self.pauses:
                raise ValueError("a clock that never started has nothing to pause")
            edge = self.started_at
        elif self.clock_started_at < self.started_at:
            raise ValueError("a clock starts no earlier than its sitting")
        else:
            edge = self.clock_started_at
        for index, one in enumerate(self.pauses):
            if one.at < edge:
                raise ValueError("a pause starts after the clock and after the pause before it")
            if one.until is None and index != len(self.pauses) - 1:
                raise ValueError("only the last pause is open")
            edge = one.until or one.at
        if self.ended_at is None:
            return self
        if self.ended_at < edge:
            raise ValueError("a sitting ends after its last pause")
        if self.paused:
            raise ValueError("a sitting ends with no pause open")
        return self
