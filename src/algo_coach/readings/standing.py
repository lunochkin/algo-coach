from collections.abc import Iterable

from algo_coach.schema import ReadingSource, TechniqueReading


def latest_by_solution(readings: Iterable[TechniqueReading]) -> dict[str, TechniqueReading]:
    """The last reading of each solution, append order breaking a tie on time.
    Within one writer only; which writer wins is `standing_readings`."""
    standing: dict[str, TechniqueReading] = {}
    for reading in readings:
        current = standing.get(reading.solution_id)
        if current is None or reading.created_at >= current.created_at:
            standing[reading.solution_id] = reading
    return standing


def standing_readings(readings: Iterable[TechniqueReading]) -> dict[str, TechniqueReading]:
    """The reading that stands on each solution: the user's own if any, however
    late the machine's."""
    readings = list(readings)
    return latest_by_solution(readings) | latest_by_solution(
        [reading for reading in readings if reading.source is ReadingSource.USER]
    )
