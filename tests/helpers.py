"""Shared fixtures for the classifier tests: a model that answers from a
script, and the two records a verdict needs to exist."""

import json
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from algo_coach.calls import Reply
from algo_coach.claims import PIN, TEMPERATURE, Configuration
from algo_coach.mint import classifier_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Problem, TechniqueClaim

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
    pin: str = PIN,
    temperature: float | None = TEMPERATURE,
    cost: float | None = None,
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
        pin=pin,
        temperature=temperature,
        cost=cost,
    )


@dataclass
class Verdict:
    """One reply the fake model gives, or one failure it raises."""

    techniques: list[str] | None = None
    error: Exception | None = None
    # What ended the reply. `length` is the token cap, where whatever came
    # back is truncated — with `text`, the runaway that emits whitespace until
    # it runs out, and without, the reply that never reached the schema.
    stop_reason: str = "stop"
    text: str | None = None


@dataclass
class FakeTransport:
    """Records the request rather than making one — the prompt is what these
    tests are about, and a real call would score a live model.

    Two scripts, because a run has two shapes. `answering` replies in call
    order, which is what a single configuration produces and what most of
    these tests read. `per_deployment` replies by which model and endpoint
    asked, which is the
    only script that survives configurations running at once: with several in
    flight, the order calls arrive in is not a fact a test can assert.
    """

    replies: list[Verdict]
    # Keyed by model and pin, which is the unit that runs beside another. One
    # model on two endpoints is two readers, and a script keyed on the model
    # alone would answer for both. A list of one answers every call from that
    # deployment, which is the ordinary case.
    scripted: dict[tuple[str, str], list[Verdict]] | None = None
    calls: list[dict] = field(default_factory=list)
    # What the router would charge. One number for every call, since what a
    # test asks about is whether the price reaches the record, never how it
    # varies.
    cost: float | None = None
    # Input, output and the thinking split, as a router would report them.
    tokens: tuple[int | None, int | None, int | None] = (None, None, None)
    # What the answering request took. A list is drawn in call order, for the
    # tests about the slowest of several.
    request_ms: int | list[int] | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def answering(cls, *verdicts: Verdict) -> FakeTransport:
        return cls(list(verdicts))

    @classmethod
    def per_deployment(
        cls, scripts: Mapping[tuple[str, str], Verdict | Sequence[Verdict]]
    ) -> FakeTransport:
        """A script per deployment. Which of two reaches the transport first is
        the scheduler's, so one shared script would make the verdicts depend on
        it. Within a deployment the order is the run's, so a list serves."""
        return cls(
            [],
            scripted={
                key: list(script) if isinstance(script, Sequence) else [script]
                for key, script in scripts.items()
            },
        )

    def asked(self, field: str) -> set:
        """What was sent for one field, as a set — the shape an assertion
        takes once the order calls were made in stops being determinate."""
        with self.lock:
            return {call.get(field) for call in self.calls}

    def __call__(self, **kwargs) -> Reply:
        with self.lock:
            self.calls.append(kwargs)
            if self.scripted is None:
                verdict = self.replies[len(self.calls) - 1]
            else:
                script = self.scripted[kwargs["model"], kwargs["pin"]]
                verdict = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(self.request_ms, list):
            taken = self.request_ms[min(len(self.calls) - 1, len(self.request_ms) - 1)]
        else:
            taken = self.request_ms
        if verdict.error is not None:
            raise verdict.error
        return Reply(
            text=(
                verdict.text
                if verdict.text is not None or verdict.techniques is None
                else json.dumps({"techniques": verdict.techniques})
            ),
            stop_reason=verdict.stop_reason,
            provider="fake",
            cost=self.cost,
            input_tokens=self.tokens[0],
            output_tokens=self.tokens[1],
            reasoning_tokens=self.tokens[2],
            request_ms=taken,
        )


def seed_problem(root, *, id: str, techniques: list[str]) -> None:
    ProblemStore(root).put(
        Problem(
            id=id,
            title=id,
            title_slug=id,
            statement="Given an array, return ...",
            techniques=techniques,
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
        user_id="u1",
        problem_id=problem_id,
        finished_at=finished_at,
        solved=True,
        code=code,
    )
