from typing import ClassVar

from pydantic import BaseModel


class MachineProvenance(BaseModel):
    """The configuration a reading was taken at, and the call that took it.
    Optional here and required by the record's own validator, since the
    hand-written counterpart carries none of it."""

    model: str | None = None
    effort: str | None = None  # how hard it was asked to think
    prompt_hash: str | None = None  # the digest of the text this record was sent
    call_id: str | None = None  # the call carrying the prompt, the tokens, the reasoning
    pin: str | None = None  # the endpoint, named to the quantization
    provider: str | None = None  # who served it, as the router reported; never compared
    temperature: float | None = None  # outside the all-or-none rule: absent is a real answer
    cost: float | None = None  # outside it too: recorded where known, never required

    PROVENANCE: ClassVar[tuple[str, ...]] = ("model", "effort", "pin", "prompt_hash", "call_id")
    RECORDED: ClassVar[tuple[str, ...]] = (*PROVENANCE, "provider", "temperature", "cost")

    def check_provenance(self, machine: bool) -> None:
        """All of it on a machine reading, none of it on a hand one."""
        named = [field for field in self.RECORDED if getattr(self, field) is not None]
        if machine:
            missing = [field for field in self.PROVENANCE if field not in named]
            if missing:
                raise ValueError(f"a machine reading needs {', '.join(missing)}")
        elif named:
            raise ValueError(f"a hand reading carries no {', '.join(named)}")
