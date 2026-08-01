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
    already the code — so the alias file only has to hold what it misses. A tag
    that reaches neither is not an error: it stays in `source_tags` and
    produces no code, because a metadata mismatch must never cost an attempt.

    Sorted and deduplicated, so re-deriving is stable regardless of the order
    the platform sent its tags in.
    """
    known = codes()
    mapped = set()
    for tag in tags:
        candidate = normalise(tag)
        candidate = aliases().get(candidate, candidate)
        if candidate in known:
            mapped.add(candidate)
    return sorted(mapped)
