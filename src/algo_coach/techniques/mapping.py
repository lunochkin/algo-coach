import json
import re
from collections.abc import Iterable
from functools import cache
from importlib import resources

from algo_coach.techniques.vocabulary import codes

_SEPARATORS = re.compile(r"[^a-z0-9]+")


@cache
def aliases() -> dict[str, str]:
    """Foreign tags that normalisation alone cannot reach: abbreviations and
    the platform's own synonyms."""
    raw = resources.files("algo_coach.techniques").joinpath("tag_map.json").read_text()
    return json.loads(raw)


def normalise(tag: str) -> str:
    return _SEPARATORS.sub("-", tag.strip().lower()).strip("-")


def map_tags(tags: Iterable[str]) -> list[str]:
    """Derive engine technique codes from an origin platform's tags.

    Normalisation carries most tags on its own — "Dynamic Programming" is
    already the code — so the alias file holds only what it misses. A tag that
    reaches neither produces no code and blocks nothing: a metadata mismatch
    must never cost an attempt.

    Sorted and deduplicated, so re-deriving is stable however the platform
    ordered its tags.
    """
    known = codes()
    mapped = set()
    for tag in tags:
        candidate = normalise(tag)
        candidate = aliases().get(candidate, candidate)
        if candidate in known:
            mapped.add(candidate)
    return sorted(mapped)
