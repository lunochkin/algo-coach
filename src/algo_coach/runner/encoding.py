"""JSON equality with sorted keys, the rule `child.encode` shares."""

import json
from typing import Any


def as_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def agrees(one: Any, other: Any) -> bool:
    return as_json(one) == as_json(other)
