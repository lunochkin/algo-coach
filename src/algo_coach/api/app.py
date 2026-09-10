from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from algo_coach.sitting import Missing, Refused


def create_app(root: Path, *, user_id: str) -> FastAPI:
    app = FastAPI(title="algo-coach")
    app.state.root = root
    # one user stands in for authentication until Phase 9 keys the log by user
    app.state.user_id = user_id
    app.add_exception_handler(Refused, _refused)
    return app


def _root(request: Request) -> Path:
    return request.app.state.root


def _user_id(request: Request) -> str:
    return request.app.state.user_id


Root = Annotated[Path, Depends(_root)]
UserId = Annotated[str, Depends(_user_id)]


async def _refused(_: Request, error: Exception) -> JSONResponse:
    # only a refusal: a bare `ValueError` is also a defect the engine raised,
    # and stays a 500
    status = 404 if isinstance(error, Missing) else 409
    return JSONResponse({"detail": str(error)}, status_code=status)
