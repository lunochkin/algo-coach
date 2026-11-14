from pydantic import model_validator

from climb.schema.attempt import FailureMode
from climb.schema.provenance import MachineProvenance
from climb.schema.record import AttemptRecord


class Diagnosis(AttemptRecord, MachineProvenance):
    """Why an attempt failed, inferred. The machine counterpart of
    `SelfLabel`."""

    mode: FailureMode
    evidence: str  # what the verdict cites: a timeout, a compile error

    @model_validator(mode="after")
    def _provenance_required(self) -> Diagnosis:
        """A model wrote every diagnosis, so there is no user arm to exempt."""
        self.check_provenance(True)
        return self
