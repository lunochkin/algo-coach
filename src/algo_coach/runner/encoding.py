"""JSON equality with sorted keys, the rule `child.encode` shares."""

import json
from typing import Any


def as_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def weighs(value: Any) -> int:
    """What a value costs on disk, as the case ceiling counts it."""
    return len(as_json(value).encode())


def agrees(one: Any, other: Any) -> bool:
    return as_json(one) == as_json(other)
