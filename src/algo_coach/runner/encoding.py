"""The rule that decides whether two answers are one.

A case is decided by JSON equality on the returned value, encoded with sorted
keys. A tuple and a list are one answer under that rule, where `True` and `1`
are two.

It lives here rather than beside either caller, because the child encodes a
return with the same rule. A second encoder would decide the same return
differently by where it ran.
"""

import json
from typing import Any


def as_json(value: Any) -> str:
    """A value as the case will store it.

    A value JSON cannot hold is not a case at all, and the encoder raising
    here says so.
    """
    return json.dumps(value, sort_keys=True)


def agrees(one: Any, other: Any) -> bool:
    return as_json(one) == as_json(other)
