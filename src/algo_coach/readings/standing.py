from collections.abc import Iterable
from operator import attrgetter

from algo_coach.schema import ReadingSource, TechniqueReading
from algo_coach.standing import standing

# Weakest first: the user's reading adjudicates the machine's.
BY_WHAT_EACH_KNEW = (ReadingSource.CLASSIFIER, ReadingSource.USER)


def standing_readings(readings: Iterable[TechniqueReading]) -> dict[str, TechniqueReading]:
    """The reading that stands on each solution: the user's own if any, however
    late the machine's."""
    return standing(readings, attrgetter("solution_id"), by_what_each_knew=BY_WHAT_EACH_KNEW)
