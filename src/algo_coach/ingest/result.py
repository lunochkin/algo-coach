from pydantic import BaseModel, Field, ValidationError


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


class CardSeedResult(BaseModel):
    ingested: int = 0
    updated: int = 0  # a slug already seeded; the card refreshes, its id stays
    rejected: list[Rejected] = Field(default_factory=list)


def reason(exc: ValidationError) -> str:
    """Flatten to one line: pydantic's own rendering is a multi-line block,
    which reads badly inside JSON a client has to parse."""
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )
