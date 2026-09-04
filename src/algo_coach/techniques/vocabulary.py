import json
from collections.abc import Mapping
from functools import cache
from importlib import resources
from types import MappingProxyType

from algo_coach.schema import Technique


@cache
def criteria() -> Mapping[str, Technique]:
    """Each code with what earns it, read through `importlib.resources` rather
    than a path relative to the working directory: it ships inside the
    wheel."""
    raw = json.loads(
        resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    )
    entries = [Technique.model_validate(entry) for entry in raw["techniques"]]
    return MappingProxyType({entry.code: entry for entry in entries})


def criterion(code: str) -> list[str]:
    """One code's rule in the words both annotators meet, and nothing for a
    code the vocabulary no longer carries: records outlive it, so a retired
    code can still be a candidate and then reaches its reader as a bare
    name."""
    entry = criteria().get(code)
    if entry is None:
        return []
    return [
        f"{entry.code} — {entry.kind}: {entry.kind.test}.",
        f"  Earns it: {entry.earns}",
        f"  Near miss: {entry.near_miss}",
    ]


@cache
def codes() -> frozenset[str]:
    return frozenset(criteria())


# The write path only: records already in the log may carry codes this rejects,
# and must still load.
def is_known(code: str) -> bool:
    return code in codes()
