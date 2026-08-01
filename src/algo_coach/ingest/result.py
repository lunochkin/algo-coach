from collections.abc import Mapping

from pydantic import BaseModel, Field, ValidationError

MISSING_EXTERNAL_ID = "external_id is required on the push path"


class Rejected(BaseModel):
    index: int  # position in the pushed batch, so the client can find the line
    reason: str


class AttemptIngestResult(BaseModel):
    ingested: int = 0
    duplicates: int = 0  # already in the log; a no-op, not an error
    rejected: list[Rejected] = Field(default_factory=list)


class ProblemIngestResult(BaseModel):
    ingested: int = 0
    updated: int = 0  # problems are a cache, so a re-push refreshes
    rejected: list[Rejected] = Field(default_factory=list)


def external_id_of(raw: Mapping) -> str | None:
    """The client's idempotency token, required on every push path."""
    value = raw.get("external_id")
    return value if isinstance(value, str) and value else None


def engine_payload(raw: Mapping, *, owned: frozenset[str], values: dict) -> dict:
    """Strip the fields the engine assigns, then apply its own.

    Stripped rather than overwritten: a derived field carried over from the
    stored record would otherwise lose to the client's value.
    """
    return {key: value for key, value in raw.items() if key not in owned} | values


def reason(exc: ValidationError) -> str:
    """Flatten to one line: pydantic's own rendering is a multi-line block,
    which reads badly inside JSON a client has to parse."""
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
