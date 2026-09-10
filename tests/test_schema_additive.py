import json
import os
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    AttemptVerification,
    Call,
    Card,
    Diagnosis,
    Draft,
    Problem,
    SelfLabel,
    SiteOutcome,
    Sitting,
    Solution,
    SolutionClaim,
    TemplateMatch,
    TestCase,
    Verification,
)

# every record a store holds. Seeds and configurations are inputs, not records
RECORDS: list[type[BaseModel]] = [
    Attempt,
    AttemptClaim,
    SelfLabel,
    Diagnosis,
    Call,
    Card,
    TestCase,
    Problem,
    Solution,
    SolutionClaim,
    TemplateMatch,
    SiteOutcome,
    Verification,
    Draft,
    Sitting,
    AttemptVerification,
]
SNAPSHOTS = Path(__file__).parent / "schemas"

# what a property's schema carries that a record already stored does not depend
# on
PROSE = ("title", "description", "default", "examples")


def shapes(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The record and every model it nests, each as its properties, its
    required names and its enum members, keyed by name."""
    found = {"": schema, **schema.get("$defs", {})}
    return {
        name: {
            "properties": {
                prop: {k: v for k, v in body.items() if k not in PROSE}
                for prop, body in one.get("properties", {}).items()
            },
            "required": set(one.get("required", [])),
            "enum": set(one.get("enum", [])),
        }
        for name, one in found.items()
    }


@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record.__name__)
def test_a_schema_change_is_additive(record: type[BaseModel]):
    """`README.md`: a change adds an optional field, and never removes one,
    requires one that was not, changes what one holds or drops an enum
    member, since the stored log has to stay readable by its own schema.

    The snapshot under `tests/schemas/` is the shape as last agreed. An
    intended tightening rewrites it in the same commit: `just schemas`.
    """
    path = SNAPSHOTS / f"{record.__name__}.json"
    live = record.model_json_schema()
    if os.environ.get("SCHEMA_SNAPSHOT") == "write" or not path.exists():
        path.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
    agreed = shapes(json.loads(path.read_text()))
    now = shapes(live)

    for key, was in agreed.items():
        name = key or record.__name__
        assert key in now, f"{name} is gone"
        here = now[key]
        assert set(was["properties"]) <= set(here["properties"]), f"{name}: a field was removed"
        assert here["required"] <= was["required"], f"{name}: a field became required"
        assert was["enum"] <= here["enum"], f"{name}: an enum member was removed"
        for prop, shape in was["properties"].items():
            assert here["properties"][prop] == shape, f"{name}.{prop}: what it holds changed"
