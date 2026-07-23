from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema.attempt import FailureMode


class Diagnosis(BaseModel):
    """Classifier verdict for one attempt; keyed to Attempt.id. Append-only,
    same rules as Attempt. Model and prompt versions are recorded so eval
    numbers stay attributable."""

    attempt_id: str
    mode: FailureMode
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    model: str
    prompt_version: str
    created_at: datetime
