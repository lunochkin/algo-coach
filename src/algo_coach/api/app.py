from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from algo_coach.api.reads import router as reads
from algo_coach.api.signin import SignIn, install
from algo_coach.api.writes import router as writes
from algo_coach.sitting import Missing, Refused
from algo_coach.storage import Database

# the path whatever serves the pages routes to the API, on the pages' origin
PREFIX = "/api"


def create_app(root: Database, *, user_id: str, sign_in: SignIn | None = None) -> FastAPI:
    app = FastAPI(title="algo-coach")
    app.state.root = root
    # one user stands in for authentication until Phase 9 keys the log by user
    app.state.user_id = user_id
    app.add_exception_handler(Refused, _refused)
    app.include_router(reads, prefix=PREFIX)
    app.include_router(writes, prefix=PREFIX)
    if sign_in is not None:
        install(app, sign_in, PREFIX)
    return app


async def _refused(_: Request, error: Exception) -> JSONResponse:
    # only a refusal: a bare `ValueError` is also a defect the engine raised,
    # and stays a 500
    status = 404 if isinstance(error, Missing) else 409
    return JSONResponse({"detail": str(error)}, status_code=status)
