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


def criterion(code: str) -> list[str]:
    """One code's rule in the words both annotators meet, and nothing for a
    code the vocabulary no longer carries. Records outlive the vocabulary, so a
    retired code can still be a candidate; it then reaches its reader as a bare
    name, which is what was said before any criterion existed.

    Rendered here rather than by each reader, because one rulebook and two
    annotators is what makes their disagreement mean something: two renderers
    would drift, and a disagreement would stop being about the code.

    The kind arrives as its test rather than as its name: one question is
    answered four ways, and a bare label only helps whoever already knows
    which way. Naming it is what keeps a structure from being judged on
    whether it was performed.
    """
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


def is_known(code: str) -> bool:
    """Membership for the write path only. Records already in the log may
    carry codes this returns False for, and must still load."""
    return code in codes()
