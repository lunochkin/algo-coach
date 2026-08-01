from pydantic import BaseModel, Field


class Technique(BaseModel):
    """A code from the product-owned vocabulary. Codes are referenced by the
    append-only log, so they are retired through an alias map, never deleted."""

    code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
