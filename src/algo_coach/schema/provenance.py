"""What produced a machine reading, on whatever record holds one.

A technique claim reads one attempt's code, a template match reads one problem
against one form. Different questions, one rule about what a re-run has to know
to find the readings it supersedes — so the fields and the all-or-none check
live here rather than being written out twice and drifting apart.
"""

from typing import ClassVar

from pydantic import BaseModel


class MachineProvenance(BaseModel):
    """The configuration a reading was taken at, and the call that took it.

    Copied onto the record rather than reached through the call, so the log
    reads on its own: a board renders from it, and loading the calls to learn
    which model answered would put a megabyte-scale read on every command. The
    copy cannot drift, since a call is append-only and the copy is made in the
    same write.

    Every field is optional here and required by the record's own validator,
    because the hand-written counterpart carries none of them.
    """

    model: str | None = None
    effort: str | None = None  # how hard it was asked to think
    prompt_hash: str | None = None  # the digest of the text this record was sent
    call_id: str | None = None  # the call carrying the rest: the prompt, the tokens, the reasoning
    # Which build read it. Quantization changes the weights, so a reading from
    # an fp4 endpoint does not answer for a bf16 one — which makes this part of
    # the configuration rather than a note about routing.
    pin: str | None = None
    # Who served it, as the router reported. Recorded and never compared: it is
    # unknown when a reader asks what it has already read, and a company name
    # cannot be checked against an endpoint anyway.
    provider: str | None = None
    # Outside the all-or-none rule: `None` is a real answer here — the
    # provider's own default — where on the other five it is a gap. Every
    # reading taken before the field existed sits in that arm, which is what
    # keeps them comparable with a greedy run instead of discarded.
    temperature: float | None = None

    PROVENANCE: ClassVar[tuple[str, ...]] = ("model", "effort", "pin", "prompt_hash", "call_id")
    RECORDED: ClassVar[tuple[str, ...]] = (*PROVENANCE, "provider", "temperature")

    def check_provenance(self, machine: bool) -> None:
        """All of it on a machine reading, none of it on a hand one.

        A machine reading is re-derivable, so it must say by what; one missing
        a field cannot be compared with one that has it, and a reader would
        branch on the absence forever. On a hand reading any of it would name a
        configuration that never touched the record, since nothing re-derives
        it.
        """
        named = [field for field in self.RECORDED if getattr(self, field) is not None]
        if machine:
            missing = [field for field in self.PROVENANCE if field not in named]
            if missing:
                raise ValueError(f"a machine reading needs {', '.join(missing)}")
        elif named:
            raise ValueError(f"a hand reading carries no {', '.join(named)}")
