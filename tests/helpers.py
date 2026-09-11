"""Shared fixtures for the classifier tests: a model that answers from a
script, and the two records a verdict needs to exist."""

import json
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from algo_coach.api import create_app
from algo_coach.api.context import SESSION_COOKIE
from algo_coach.calls import CallLog, Reply
from algo_coach.cards import CardStore
from algo_coach.classifier import PIN, TEMPERATURE
from algo_coach.log import AttemptLog, named, opened
from algo_coach.mint import classifier_claim, user_solution_claim
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    Call,
    Card,
    Configuration,
    MachineProvenance,
    Problem,
    Selector,
    Solution,
    SolutionRole,
    Template,
)
from algo_coach.solution_claims import SolutionClaimLog
from algo_coach.solutions import SolutionLog

T0 = datetime(2026, 1, 1, tzinfo=UTC)

# The configuration `machine_claim` defaults to, so a test can look a claim up
# without restating what produced it.
CONFIGURATION = Configuration(model="a-model", effort="medium", pin=PIN, temperature=TEMPERATURE)

# The prompt hash `machine_claim` defaults to. A test naming a different one is
# saying the prompt changed, which is the only thing that makes a claim stale.
PROMPT_HASH = "0123456789ab"

# What a generated problem carries. Spelled out once: a problem carries
# provenance unconditionally, so a site restating the five fields would say
# nothing about what its test is for.
PROVENANCE_FIELDS = {
    "model": "a-model",
    "effort": "medium",
    "pin": PIN,
    "prompt_hash": PROMPT_HASH,
    "call_id": "call-1",
}

# Provenance and a technique target. A site caring about neither spreads this.
# A technique rather than a template, so a stored problem names no card: one
# testing a template's target names its own, and stores the card
GENERATED = PROVENANCE_FIELDS | {"target_technique": "greedy"}

# The same, as the record a minter takes.
PROVENANCE = MachineProvenance(**PROVENANCE_FIELDS)

# The call `PROVENANCE` cites, as the database fixture stores it before every
# test.
CALL_ROW = {
    "id": "call-1",
    "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    "model": "a-model",
    "effort": "medium",
    "pin": PIN,
    "prompt": "a prompt",
    "prompt_hash": PROMPT_HASH,
    "response": "{}",
}


def a_call(id: str = "call-1", **overrides) -> Call:
    """One recorded request. A case, a solution and a problem all copy a call's
    configuration, so a test that is not about provenance takes this one."""
    fields = {
        "id": id,
        "created_at": T0,
        "model": "a-model",
        "effort": "medium",
        "prompt": "a prompt",
        "prompt_hash": PROMPT_HASH,
        "response": "{}",
        "pin": PIN,
        "provider": "a-provider",
    } | overrides
    return Call.model_validate(fields)


def make_problem(id: str = "p1", **overrides) -> Problem:
    """A generated problem, its provenance and its template defaulted."""
    fields = (
        {
            "id": id,
            "title": id,
            "statement": "Given an array, return ...",
        }
        | GENERATED
        | overrides
    )
    return Problem.model_validate(fields)


def machine_claim(
    attempt_id: str,
    techniques: list[str],
    *,
    model: str = "a-model",
    effort: str = "medium",
    prompt_hash: str = PROMPT_HASH,
    call_id: str | None = None,
    pin: str = PIN,
    temperature: float | None = TEMPERATURE,
    cost: float | None = None,
) -> AttemptClaim:
    """A classifier claim under a named configuration, defaulted so a test
    naming one field says that field is what it is about. The call it names is
    one per configuration, as a run makes, unless the test names one."""
    configuration = (model, effort, prompt_hash, pin, temperature, cost)
    return classifier_claim(
        attempt_id,
        techniques,
        provenance=MachineProvenance(
            model=model,
            effort=effort,
            prompt_hash=prompt_hash,
            call_id=call_id or "call-" + "-".join(str(one) for one in configuration),
            pin=pin,
            temperature=temperature,
            cost=cost,
        ),
    )


@dataclass
class Verdict:
    """One reply the fake model gives, or one failure it raises. The names go
    under whatever key the request's schema asks for, so one fake answers the
    classifier and the matcher alike."""

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
    # Input, output and the reasoning split, as a router would report them.
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
        key = next(iter((kwargs.get("schema") or {}).get("required", [])), "techniques")
        return Reply(
            text=(
                verdict.text
                if verdict.text is not None or verdict.techniques is None
                else json.dumps({key: verdict.techniques})
            ),
            stop_reason=verdict.stop_reason,
            provider="fake",
            cost=self.cost,
            input_tokens=self.tokens[0],
            output_tokens=self.tokens[1],
            reasoning_tokens=self.tokens[2],
            request_ms=taken,
        )


def seed_problem(root, *, id: str, techniques: list[str], **problem) -> None:
    """A stored problem deriving `techniques`: one canonical, read by hand as
    using them. The record itself carries none, as a generated one does."""
    ProblemStore(root).put(make_problem(id, **problem))
    canonical = Solution(
        id=f"{id}-canonical",
        created_at=T0,
        problem_id=id,
        role=SolutionRole.CANONICAL,
        code="def solve(xs):\n    return sorted(xs)\n",
        **PROVENANCE_FIELDS,
    )
    SolutionLog(root).append(canonical)
    SolutionClaimLog(root).append(user_solution_claim(canonical.id, techniques))


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


def own(records: list) -> list:
    """What a test wrote, without the rows the database fixture stores for the
    shared helpers."""
    shared = {CALL_ROW["id"]}
    return [one for one in records if one.id not in shared]


def stored_problem(root, id: str = "p1", **overrides) -> Problem:
    """A problem in the store, for a record whose foreign key names it. Storing
    one already there changes nothing."""
    problem = make_problem(id, **overrides)
    ProblemStore(root).put(problem)
    return problem


def stored_solution(root, id: str = "s1", problem_id: str = "p1") -> Solution:
    """A canonical in the store, and the problem it answers."""
    stored_problem(root, problem_id)
    solution = Solution(
        id=id,
        created_at=T0,
        problem_id=problem_id,
        role=SolutionRole.CANONICAL,
        code="def solve(xs):\n    return sorted(xs)\n",
        **PROVENANCE_FIELDS,
    )
    SolutionLog(root).append(solution)
    return solution


def stored_template(root, id: str = "t1") -> None:
    """A card holding one template of this id, for a record naming the
    template."""
    template = Template(id=id, slug=id, title=id, trigger="a trigger", code="def f(): pass")
    CardStore(root).put(
        Card(
            id=f"card-{id}",
            slug=f"card-{id}",
            technique="greedy",
            title=id,
            trigger="a trigger",
            brief="a brief",
            templates=[template],
            selector=Selector(technique="greedy", size=1),
        )
    )


def logged(log, claim: AttemptClaim) -> None:
    """A claim appended, with the call it names stored first where none of that
    id is, since a machine claim reads its configuration off its call."""
    if claim.call_id is not None:
        calls = CallLog(log.root)
        if all(held.id != claim.call_id for held in calls.all()):
            calls.append(
                a_call(
                    claim.call_id,
                    model=claim.model,
                    effort=claim.effort,
                    prompt_hash=claim.prompt_hash,
                    pin=claim.pin,
                    provider=claim.provider,
                    temperature=claim.temperature,
                    cost=claim.cost,
                )
            )
    log.append_claim(claim)


def stored_attempt(root, id: str = "a1", problem_id: str = "p1", user_id: str = "u1") -> Attempt:
    """An attempt in the log, and the problem it names, for a record keyed to
    it."""
    stored_problem(root, problem_id)
    one = Attempt(
        id=id, user_id=user_id, problem_id=problem_id, finished_at=T0, solved=True, code="pass"
    )
    AttemptLog(root).append_attempt(one)
    return one


def browsing(database, user_id: str, **options) -> TestClient:
    """The app, from a browser signed in as the user: a session opened for it,
    its token in the cookie a sign-in sets."""
    named(database, user_id)
    # as the pages send every request: the API refuses a write that is not JSON
    headers = {"content-type": "application/json"}
    client = TestClient(create_app(database), headers=headers, **options)
    client.cookies.set(SESSION_COOKIE, opened(database, user_id))
    return client
