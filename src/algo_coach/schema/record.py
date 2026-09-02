from datetime import datetime

from pydantic import BaseModel


class AttemptRecord(BaseModel):
    """What every append-only record keyed to an attempt carries."""

    id: str
    created_at: datetime
    attempt_id: str
