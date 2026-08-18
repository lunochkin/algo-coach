from enum import StrEnum

from pydantic import BaseModel, Field


class ProblemOwner(StrEnum):
    PRODUCT = "product"
    USER = "user"


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Problem(BaseModel):
    id: str  # engine-minted; never accepted from a client
    # (external_id, user_id) — idempotency key for user-owned problems
    external_id: str | None = None
    user_id: str | None = None
    owner: ProblemOwner
    title: str
    title_slug: str
    url: str | None = None
    platform: str | None = None
    # tags as the origin platform sent them; techniques are derived from them
    # by the engine's mapping and may be re-derived at any time
    source_tags: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)
    difficulty: ProblemDifficulty | None = None
    # what the problem asks, where tags say what it is about; matching reads it
    statement: str = Field(min_length=1)
