import json
from functools import cache
from importlib import resources

from algo_coach.schema import Technique


@cache
def codes() -> frozenset[str]:
    """The product-owned technique vocabulary.

    Read through `importlib.resources` rather than a path relative to the
    working directory: it ships inside the wheel and has to resolve wherever
    the CLI runs.
    """
    raw = json.loads(
        resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    )
    return frozenset(Technique.model_validate({"code": code}).code for code in raw["techniques"])


def is_known(code: str) -> bool:
    """Membership for the write path only. Records already in the log may
    carry codes this returns False for, and must still load."""
    return code in codes()
