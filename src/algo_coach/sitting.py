"""One timed session on one problem: what the drill loop serves, judges and
mints. `log.md` gives what the record holds and why a pause is an interval."""

from datetime import UTC, datetime

from algo_coach.log import SittingStore
from algo_coach.schema import Pause, Sitting

# the cap a sitting judges a submission under. The speedup search picks the
# separating size against it, and generation's own cap sits well above it
DRILL_CAP_MS = 2_000


def pause(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    if one.paused:
        raise ValueError(f"sitting {sitting_id} is already paused")
    return _stored(store, one, pauses=[*one.pauses, Pause(at=now or _clock())])


def resume(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    if not one.paused:
        raise ValueError(f"sitting {sitting_id} is not paused")
    return _stored(store, one, pauses=_closed(one.pauses, now or _clock()))


def end(store: SittingStore, sitting_id: str, *, now: datetime | None = None) -> Sitting:
    one = _running(store, sitting_id)
    at = now or _clock()
    # a pause the user never resumed covers the time away, and closing it here
    # is what leaves the sitting ended with none open
    return _stored(
        store, one, pauses=_closed(one.pauses, at) if one.paused else one.pauses, ended_at=at
    )


def _running(store: SittingStore, sitting_id: str) -> Sitting:
    one = store.get(sitting_id)
    if one is None:
        raise ValueError(f"no sitting {sitting_id}")
    if one.ended_at is not None:
        raise ValueError(f"sitting {sitting_id} has ended")
    return one


def _closed(pauses: list[Pause], at: datetime) -> list[Pause]:
    return [*pauses[:-1], Pause(at=pauses[-1].at, until=at)]


def _stored(store: SittingStore, one: Sitting, **changes: object) -> Sitting:
    # revalidated rather than copied: `model_copy` would write a record the
    # interval rules never read
    revised = Sitting.model_validate(one.model_dump() | changes)
    store.put(revised)
    return revised


def _clock() -> datetime:
    return datetime.now(UTC)
