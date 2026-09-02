"""Which stored readings a given classifier produced, at a given question."""

from collections.abc import Iterable, Mapping, Sequence

from algo_coach.classifier import Configuration
from algo_coach.schema import ReadingSource, Solution, TechniqueReading


def at_configuration(
    reading: TechniqueReading, configuration: Configuration, prompt_hash: str
) -> bool:
    """Whether this classifier, asked this question, produced the record. The
    provider that served it is recorded and never compared, and a hand reading
    is at no configuration at all."""
    if reading.source is not ReadingSource.CLASSIFIER:
        return False
    return (
        reading.model,
        reading.effort,
        reading.pin,
        reading.temperature,
        reading.prompt_hash,
    ) == (
        configuration.model,
        configuration.effort,
        configuration.pin,
        configuration.temperature,
        prompt_hash,
    )


def outstanding(
    solutions: Sequence[Solution],
    readings: Iterable[TechniqueReading],
    hashes: Mapping[str, str],
    *,
    configuration: Configuration,
) -> list[Solution]:
    """The solutions this configuration has not read as it would ask now.
    `hashes` is what each would be sent, keyed by solution. Any record at that
    text answers, latest or not: a re-run buys the same verdict."""
    read = {
        reading.solution_id
        for reading in readings
        if reading.solution_id in hashes
        and at_configuration(reading, configuration, hashes[reading.solution_id])
    }
    return [solution for solution in solutions if solution.id not in read]
