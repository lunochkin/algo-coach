from pydantic import Field

from algo_coach.schema.attempt import FailureMode
from algo_coach.schema.record import AttemptRecord


class Diagnosis(AttemptRecord):
    """Why an attempt went the way it did, inferred rather than reported.

    The machine counterpart of `SelfLabel`, and never a substitute for it: the
    eval scores a diagnosis against the user's own verdict, so neither
    supersedes the other. Model and prompt version are recorded so an attempt
    can be re-diagnosed and the numbers stay attributable.
    """

    mode: FailureMode
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    model: str
    prompt_version: str
