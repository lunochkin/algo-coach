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
    """The client's idempotency token. Required on every push path, so its
    absence is the one rejection both ingests raise before validating."""
    value = raw.get("external_id")
    return value if isinstance(value, str) and value else None


def engine_payload(raw: Mapping, *, owned: frozenset[str], values: dict) -> dict:
    """Strip the fields the engine assigns, then apply its own.

    Stripping rather than only overwriting: a field the engine derives has to
    survive from the stored record, and a client value left in place would win.
    """
    return {key: value for key, value in raw.items() if key not in owned} | values


def reason(exc: ValidationError) -> str:
    """One line per report. Pydantic's own rendering is a multi-line block,
    which reads badly inside JSON a client has to parse."""
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
