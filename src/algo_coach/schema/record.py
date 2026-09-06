from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttemptRecord(BaseModel):
    """What every append-only record keyed to an attempt carries."""

    model_config = ConfigDict(frozen=True)

    id: str
    created_at: datetime
    attempt_id: str
