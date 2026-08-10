from enum import StrEnum

from pydantic import BaseModel, Field


class Kind(StrEnum):
    """What sort of thing a code names. One question — did the solution use
    this — is answered differently for each, so the kind selects the test."""

    PROCEDURE = "procedure"  # counts when the solution performs it
    STRUCTURE = "structure"  # counts when its properties carry the work
    PARADIGM = "paradigm"  # counts when it is why the solution is correct
    # Counts when it is what the problem asks for — read from the relation the
    # solution computes, since no statement is stored and neither annotator
    # ever sees one. The kind still separates what from how: a brute-force
    # search and a failure function are one class and two procedures.
    PROBLEM_CLASS = "problem-class"


class Technique(BaseModel):
    """A vocabulary entry: a code and the criterion for claiming it.

    Not the type of a code in a record, which is a bare string. Records carry
    retired codes forever, and a retired code has no criterion — so a model
    with these fields could not describe one. The vocabulary is checked on the
    write path instead, by `is_known`.
    """

    code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    kind: Kind
    earns: str = Field(min_length=1)
    # The load-bearing half. The disputes are boundaries rather than
    # definitions, so an entry naming only what a code is settles nothing.
    near_miss: str = Field(min_length=1)
