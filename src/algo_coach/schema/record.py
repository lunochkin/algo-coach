from datetime import datetime

from pydantic import BaseModel


class AttemptRecord(BaseModel):
    """What every append-only record keyed to an attempt carries.

    A claim, a self-label and a diagnosis are all assertions about one
    attempt, made after it and never rewritten: a later record of the same
    kind supersedes the earlier one, which stays in the log. `latest_by_attempt`
    reads any of them.

    Identity is the engine's, so a record can be referenced — by an eval
    naming the diagnosis it scored, or by a user correcting a claim.
    """

    id: str  # engine-minted; never accepted from a client
    created_at: datetime
    attempt_id: str
