import json
from functools import cache
from importlib import resources

from algo_coach.schema import Technique


@cache
def codes() -> frozenset[str]:
    """The product-owned technique vocabulary, read from the packaged file.

    Read through `importlib.resources`, not a path relative to the working
    directory: the vocabulary ships inside the wheel and has to resolve
    wherever the CLI is run from.
    """
    raw = json.loads(
        resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    )
    return frozenset(Technique.model_validate({"code": code}).code for code in raw["techniques"])


def is_known(code: str) -> bool:
    """Membership for the write path only. Records already in the log may
    carry codes this returns False for, and must still load."""
    return code in codes()
