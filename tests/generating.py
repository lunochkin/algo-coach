"""Fixtures the generation tests share: a model that answers a generation call
and a reference call apart, and the reply each of them expects."""

import json
from dataclasses import dataclass, field

from algo_coach.calls import Reply

CANONICAL = "def solve(xs):\n    return len(xs)\n"
BLIND = "def solve(xs):\n    return sum(1 for _ in xs)\n"


def draft(statement: str = "Given a list of readings, return ...", **overrides) -> str:
    return json.dumps(
        {
            "title": "Widest fair stretch",
            "statement": statement,
            "canonical": CANONICAL,
            "difficulty": "medium",
            "cases": [{"args": "[[1, 2, 3]]", "expected": "3"}],
        }
        | overrides
    )


def blind(solution: str = BLIND) -> str:
    return json.dumps({"solution": solution})


@dataclass
class FakeWriter:
    """Answers the two calls apart, telling them by what was sent: the
    reference is given the statement alone, so its content is delimited prose
    where the generation brief is a template.

    `statements` is what each generation call returns, in order; a `None` in it
    is a call that answered nothing.
    """

    statements: list[str | None] = field(default_factory=lambda: ["A statement."])
    calls: list[dict] = field(default_factory=list)
    written: int = 0

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        if kwargs["content"].startswith("<problem>"):
            return Reply(text=blind(), stop_reason="stop")
        statement = self.statements[min(self.written, len(self.statements) - 1)]
        self.written += 1
        if statement is None:
            return Reply(text=None, stop_reason="length")
        return Reply(text=draft(statement), stop_reason="stop")

    @property
    def briefs(self) -> list[str]:
        """What the generation calls were sent, in order."""
        return [one["content"] for one in self.calls if not one["content"].startswith("<problem>")]
