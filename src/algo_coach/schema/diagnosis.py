from pydantic import Field

from algo_coach.schema.attempt import FailureMode
from algo_coach.schema.record import AttemptRecord


class Diagnosis(AttemptRecord):
    """Why an attempt failed, inferred. The machine counterpart of `SelfLabel`."""

    mode: FailureMode
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    model: str
    prompt_version: str
