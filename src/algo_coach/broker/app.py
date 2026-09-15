import asyncio
import math
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Literal, Self

from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from starlette.concurrency import run_in_threadpool

from algo_coach.broker.container import (
    Clear,
    Execute,
    Stop,
    command,
    container_name,
    deadline,
    docker,
    kill,
    output_limit,
    remove_leftovers,
)

# how long a run waits for the run before it. Past it the run is refused: a
# wait with no bound reads to the user as a sandbox that hung
WAIT_SECONDS = 30.0

router = APIRouter()


class Run(BaseModel):
    """A run as the entry process reads it."""

    # the image, the mounts and the flags are the broker's source alone, so a
    # field naming one is refused rather than ignored
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    args: list[list[JsonValue]]
    cap_ms: Annotated[int, Field(gt=0)]
    repeats: list[Annotated[int, Field(gt=0)]] | None = None
    stop_early: bool = False

    @model_validator(mode="after")
    def _a_count_per_case(self) -> Self:
        if self.repeats is not None and len(self.repeats) != len(self.args):
            raise ValueError("a repeat count per argument tuple, or none at all")
        return self


class CaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["returned", "timeout", "crashed"]
    # the child's own encoding, decoded above the boundary
    value: str | None
    elapsed_ms: int | None
    error: str | None = None


class Ran(BaseModel):
    cases: list[CaseResult]


def create_app(
    execute: Execute = docker,
    stop: Stop = kill,
    clear: Clear = remove_leftovers,
    wait_seconds: float = WAIT_SECONDS,
) -> FastAPI:
    @asynccontextmanager
    async def started(_: FastAPI) -> AsyncGenerator[None]:
        # before the first run: a broker that died mid-run left its container
        # running, and nothing else ever removes it
        clear()
        yield

    app = FastAPI(title="algo-coach broker", lifespan=started)
    app.state.execute = execute
    app.state.stop = stop
    # one run at a time: a run beside another measures the contention between
    # them. The broker is one process, so one lock holds for every API worker
    app.state.admission = asyncio.Lock()
    app.state.wait_seconds = wait_seconds
    app.include_router(router)
    return app


# async for the wait alone: a waiting run holds no thread, so no pool of
# threads queues it ahead of the bound
@router.post("/run")
async def run(body: Run, request: Request) -> Ran:
    state = request.app.state
    admission: asyncio.Lock = state.admission
    wait_seconds: float = state.wait_seconds
    try:
        await asyncio.wait_for(admission.acquire(), wait_seconds)
    except TimeoutError:
        raise HTTPException(
            503,
            f"another run held the sandbox past {wait_seconds} s",
            headers={"Retry-After": str(math.ceil(wait_seconds))},
        ) from None
    try:
        # a cancelled request does not abandon the thread, so the lock is
        # released only once the container is done
        return await run_in_threadpool(_answered, body, state.execute, state.stop)
    finally:
        admission.release()


def _answered(body: Run, execute: Execute, stop: Stop) -> Ran:
    name = container_name()
    wanted = len(body.args)
    done = execute(
        command(name),
        body.model_dump_json().encode(),
        output_limit(wanted),
        deadline(wanted, body.cap_ms),
    )
    if done.how == "expired":
        # past every cap and the start: a child stuck outside Python, or an
        # entry process that stopped answering
        stop(name)
        # the last line may be cut off by the kill, and a cut line is no result
        return Ran(cases=_rest_timed_out(_cases(done.stdout.split(b"\n")[:-1], body), body))
    # a fault of the container or the entry process says nothing about the
    # solution, so it is raised and never answered as a verdict
    if done.how == "overflowed" or done.returncode != 0:
        stderr = done.stderr.decode(errors="replace")[-2000:]
        raise HTTPException(500, f"the run's container exited {done.returncode}: {stderr}")
    cases = _cases(done.stdout.splitlines(), body)
    if not body.stop_early and len(cases) < wanted:
        raise HTTPException(500, f"the entry process reported {len(cases)} of {wanted} cases")
    return Ran(cases=cases)


def _cases(lines: list[bytes], body: Run) -> list[CaseResult]:
    cases = [CaseResult.model_validate_json(line) for line in lines]
    if len(cases) > len(body.args):
        raise HTTPException(
            500, f"the entry process reported {len(cases)} of {len(body.args)} cases"
        )
    return cases


def _rest_timed_out(reported: list[CaseResult], body: Run) -> list[CaseResult]:
    """Each case the entry process never reported, read as the parent's timer
    firing: `TIMEOUT`."""
    cases = list(reported)
    while len(cases) < len(body.args):
        if body.stop_early and cases and cases[-1].outcome != "returned":
            break
        cases.append(CaseResult(outcome="timeout", value=None, elapsed_ms=None))
    return cases
