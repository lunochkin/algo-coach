from enum import StrEnum

from pydantic import BaseModel, Field


class Kind(StrEnum):
    """What sort of thing a code names. The kind selects the test."""

    PROCEDURE = "procedure"
    STRUCTURE = "structure"
    PARADIGM = "paradigm"
    PROBLEM_CLASS = "problem-class"  # read from the relation computed; no statement is stored

    @property
    def test(self) -> str:
        return _TESTS[self]


_TESTS = {
    Kind.PROCEDURE: "counts when the solution performs it",
    Kind.STRUCTURE: "counts when its properties carry the correctness or the complexity",
    Kind.PARADIGM: "counts when it is why the solution is correct",
    Kind.PROBLEM_CLASS: "counts when it is what the problem asks for",
}


class Technique(BaseModel):
    """A vocabulary entry: a code and the criterion for claiming it.
    Not the type of a code in a record, which is a bare string: a retired one
    has no criterion."""

    code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    kind: Kind
    earns: str = Field(min_length=1)
    near_miss: str = Field(min_length=1)  # the code it is confused with, which decides cases
