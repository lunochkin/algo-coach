import json
from collections.abc import Mapping
from functools import cache
from importlib import resources
from types import MappingProxyType

from algo_coach.schema import Technique


@cache
def criteria() -> Mapping[str, Technique]:
    """The product-owned technique vocabulary, each code with what earns it.

    Read through `importlib.resources` rather than a path relative to the
    working directory: it ships inside the wheel and has to resolve wherever
    the CLI runs. Read-only, because these reach a prompt and a reader
    unchanged — an entry edited in memory would be a criterion nothing recorded.
    """
    raw = json.loads(
        resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    )
    entries = [Technique.model_validate(entry) for entry in raw["techniques"]]
    return MappingProxyType({entry.code: entry for entry in entries})


@cache
def codes() -> frozenset[str]:
    return frozenset(criteria())


def is_known(code: str) -> bool:
    """Membership for the write path only. Records already in the log may
    carry codes this returns False for, and must still load."""
    return code in codes()
