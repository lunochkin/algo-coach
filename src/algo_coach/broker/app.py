from typing import Annotated, Literal, Self

from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from algo_coach.broker.container import Execute, command, docker, output_limit

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


def create_app(execute: Execute = docker) -> FastAPI:
    app = FastAPI(title="algo-coach broker")
    app.state.execute = execute
    app.include_router(router)
    return app


# sync: the container blocks, and FastAPI runs a sync route on its thread pool
@router.post("/run")
def run(body: Run, request: Request) -> Ran:
    execute: Execute = request.app.state.execute
    done = execute(command(), body.model_dump_json().encode(), output_limit(len(body.args)))
    # a fault of the container or the entry process says nothing about the
    # solution, so it is raised and never answered as a verdict
    if done.returncode != 0:
        stderr = done.stderr.decode(errors="replace")[-2000:]
        raise HTTPException(500, f"the run's container exited {done.returncode}: {stderr}")
    cases = [CaseResult.model_validate_json(line) for line in done.stdout.splitlines()]
    wanted = len(body.args)
    if len(cases) > wanted or (not body.stop_early and len(cases) < wanted):
        raise HTTPException(500, f"the entry process reported {len(cases)} of {wanted} cases")
    return Ran(cases=cases)
