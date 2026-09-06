"""JSON equality with sorted keys, the rule `child.encode` shares."""

import json

from algo_coach.schema import Json


def as_json(value: Json) -> str:
    return json.dumps(value, sort_keys=True)


def weighs(value: Json) -> int:
    """What a value costs on disk, as the case ceiling counts it."""
    return len(as_json(value).encode())


def agrees(one: Json, other: Json) -> bool:
    return as_json(one) == as_json(other)
