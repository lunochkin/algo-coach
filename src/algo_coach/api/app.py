from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from algo_coach.api.reads import router as reads
from algo_coach.api.writes import router as writes
from algo_coach.sitting import Missing, Refused


def create_app(root: Path, *, user_id: str) -> FastAPI:
    app = FastAPI(title="algo-coach")
    app.state.root = root
    # one user stands in for authentication until Phase 9 keys the log by user
    app.state.user_id = user_id
    app.add_exception_handler(Refused, _refused)
    app.include_router(reads)
    app.include_router(writes)
    return app


async def _refused(_: Request, error: Exception) -> JSONResponse:
    # only a refusal: a bare `ValueError` is also a defect the engine raised,
    # and stays a 500
    status = 404 if isinstance(error, Missing) else 409
    return JSONResponse({"detail": str(error)}, status_code=status)
