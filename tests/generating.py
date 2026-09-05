"""Fixtures the generation tests share: a model that answers a generation call
and a reference call apart, and the reply each of them expects."""

import json
from dataclasses import dataclass, field

from algo_coach.calls import Reply
from algo_coach.generation import blind, clock, discrimination, inputs

CANONICAL = "def solve(xs):\n    return len(xs)\n"
BLIND = "def solve(xs):\n    return sum(1 for _ in xs)\n"
# the clock: correct and no slower here, since a run that wants a separation
# writes its own
NAIVE = "def solve(xs):\n    return len([one for one in xs])\n"


def draft(statement: str = "Given a list of readings, return ...", **overrides) -> str:
    written = {
        "title": "Widest fair stretch",
        "statement": statement,
        "canonical": CANONICAL,
        "difficulty": "medium",
        "cases": [{"args": "[[1, 2, 3]]", "expected": "3"}],
    } | overrides
    return json.dumps(written | {"statement": signed(written["statement"], written["canonical"])})


def signed(statement: str, canonical: str) -> str:
    """The statement with the signature its canonical takes, which every
    generation call is required to end on."""
    header = canonical.split("\n", 1)[0].rstrip(":")
    return statement if "def solve(" in statement else f"{statement}\n\n{header}"


def solved(solution: str = BLIND) -> str:
    return json.dumps({"solution": solution})


def proposed(*args) -> str:
    return json.dumps({"cases": [{"args": json.dumps(list(one))} for one in args]})


# one element per size, which separates nothing: a run that wanted a timing
# case builds its own writer
def built(
    code: str = "def solve(size, seed):\n    return [list(range(size))]\n", largest: int = 8
) -> str:
    return json.dumps({"code": code, "largest": largest})


@dataclass
class FakeWriter:
    """Answers the two calls apart, telling them by what was sent: the
    reference is given the statement alone, so its content is delimited prose
    where the generation brief is a template.

    `statements` is what each generation call returns, in order; a `None` in it
    is a call that answered nothing. `solution` is what every reference call
    returns, which is what drives a run into the gates the two solutions
    decide.
    """

    statements: list[str | None] = field(default_factory=lambda: ["A statement."])
    solution: str = BLIND
    generator: str | None = None
    # what each discrimination call proposes, in order. `None` is a call that
    # answered nothing, which costs the round
    separators: list[list | None] = field(default_factory=lambda: [None])
    # the solution the mutation loop enumerates from, and the cases it runs
    # the mutants against
    canonical: str = CANONICAL
    # what every clock call returns, which is the solution the search measures
    # the canonical against
    slow: str | None = NAIVE
    cases: list[dict] | None = None
    calls: list[dict] = field(default_factory=list)
    written: int = 0
    answered: int = 0

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        # told apart by the brief rather than by the content: the reference and
        # the input generator are both handed the statement alone
        if kwargs["system"] == blind.SYSTEM:
            return Reply(text=solved(self.solution), stop_reason="stop")
        if kwargs["system"] == discrimination.SYSTEM:
            asked = self.separators[min(self.answered, len(self.separators) - 1)]
            self.answered += 1
            if asked is None:
                return Reply(text=None, stop_reason="length")
            return Reply(text=proposed(*asked), stop_reason="stop")
        if kwargs["system"] == clock.SYSTEM:
            if self.slow is None:
                return Reply(text=None, stop_reason="length")
            return Reply(text=solved(self.slow), stop_reason="stop")
        if kwargs["system"] == inputs.SYSTEM:
            if self.generator is None:
                return Reply(text=None, stop_reason="length")
            return Reply(text=built(self.generator), stop_reason="stop")
        statement = self.statements[min(self.written, len(self.statements) - 1)]
        self.written += 1
        if statement is None:
            return Reply(text=None, stop_reason="length")
        written = {"canonical": self.canonical}
        if self.cases is not None:
            written["cases"] = self.cases
        return Reply(text=draft(statement, **written), stop_reason="stop")

    @property
    def briefs(self) -> list[str]:
        """What the generation calls were sent, in order."""
        return [
            one["content"]
            for one in self.calls
            if one["system"]
            not in (blind.SYSTEM, clock.SYSTEM, discrimination.SYSTEM, inputs.SYSTEM)
        ]


class Raises(FakeWriter):
    """Answers the generation call and fails the blind one, which is the call
    that can raise once a draft exists."""

    def __call__(self, **kwargs) -> Reply:
        if kwargs["system"] == blind.SYSTEM:
            raise RuntimeError("the gateway is down")
        return super().__call__(**kwargs)
