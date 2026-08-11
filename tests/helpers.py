"""Shared fixtures for the classifier tests: a model that answers from a
script, and the two records a verdict needs to exist."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from algo_coach.claims import Configuration
from algo_coach.mint import classifier_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, AttemptOrigin, Problem, ProblemOwner, TechniqueClaim
from algo_coach.techniques import map_tags

T0 = datetime(2026, 1, 1, tzinfo=UTC)

# The configuration `machine_claim` defaults to, so a test can look a claim up
# without restating what produced it.
CONFIGURATION = Configuration(model="a-model", effort="medium")

# The digest `machine_claim` defaults to. A test naming a different one is
# saying the prompt changed, which is the only thing that makes a claim stale.
PROMPT_HASH = "0123456789ab"


def machine_claim(
    attempt_id: str,
    techniques: list[str],
    *,
    model: str = "a-model",
    effort: str = "medium",
    prompt_hash: str = PROMPT_HASH,
    call_id: str = "call-1",
) -> TechniqueClaim:
    """A classifier claim under a named configuration, defaulted so a test
    naming one field says that field is what it is about."""
    return classifier_claim(
        attempt_id,
        techniques,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
    )


@dataclass
class Verdict:
    """One reply the fake model gives, or one failure it raises."""

    techniques: list[str] | None = None
    error: Exception | None = None


@dataclass
class Block:
    text: str
    type: str = "text"


@dataclass
class Response:
    content: list[Block]
    stop_reason: str = "end_turn"


@dataclass
class FakeMessages:
    """Records the request rather than making one — the prompt is what these
    tests are about, and a real call would score a live model."""

    replies: list[Verdict]
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs) -> Response:
        self.calls.append(kwargs)
        verdict = self.replies[len(self.calls) - 1]
        if verdict.error is not None:
            raise verdict.error
        return Response([Block(json.dumps({"techniques": verdict.techniques}))])


@dataclass
class FakeClient:
    messages: FakeMessages

    @classmethod
    def answering(cls, *verdicts: Verdict) -> FakeClient:
        return cls(FakeMessages(list(verdicts)))


def seed_problem(root, *, id: str, tags: list[str]) -> None:
    ProblemStore(root).put(
        Problem(
            id=id,
            external_id=f"ext-{id}",
            user_id="u1",
            owner=ProblemOwner.USER,
            title=id,
            title_slug=id,
            source_tags=tags,
            techniques=map_tags(tags),
        )
    )


def attempt(
    id: str,
    problem_id: str,
    *,
    code: str | None = "def f(): pass",
    finished_at: datetime = T0,
) -> Attempt:
    return Attempt(
        id=id,
        external_id=f"ext-{id}",
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=True,
        origin=AttemptOrigin.PUSH,
        code=code,
    )
