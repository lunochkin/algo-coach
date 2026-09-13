from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from algo_coach.api.account import router as account
from algo_coach.api.devlogin import router as dev_login_router
from algo_coach.api.pages import Pages
from algo_coach.api.reads import router as reads
from algo_coach.api.signin import SignIn, install
from algo_coach.api.writes import router as writes
from algo_coach.sitting import Missing, Refused
from algo_coach.storage import Database

# the path whatever serves the pages routes to the API, on the pages' origin
PREFIX = "/api"
# the methods a write is sent with
WRITES = {"POST", "PUT", "PATCH", "DELETE"}


def create_app(
    root: Database,
    *,
    sign_in: SignIn | None = None,
    dev_login: str | None = None,
    pages: Path | None = None,
) -> FastAPI:
    # a deployed engine signs its users in through a provider, so a client
    # beside the dev login is a deployment the flag would open
    if dev_login is not None and sign_in is not None:
        raise ValueError("the dev login refuses to start beside a provider's client")
    app = FastAPI(title="algo-coach")
    app.state.root = root
    # what the login page offers, filled in below by what is configured
    app.state.providers = []
    app.state.dev_user = dev_login
    app.middleware("http")(_json_writes)
    app.add_exception_handler(Refused, _refused)
    app.include_router(reads, prefix=PREFIX)
    app.include_router(writes, prefix=PREFIX)
    app.include_router(account, prefix=PREFIX)
    if sign_in is not None:
        install(app, sign_in, PREFIX)
    if dev_login is not None:
        app.include_router(dev_login_router, prefix=PREFIX)
    # last, since a mount at the root answers every path the routes above left
    if pages is not None:
        app.mount("/", Pages(pages, PREFIX))
    return app


async def _json_writes(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # a form on another site sends a form's content type, and JSON from another
    # origin needs a preflight this API never answers. So a write the session
    # cookie carries is refused unless it is JSON
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if request.method in WRITES and media_type != "application/json":
        return JSONResponse({"detail": "a write is sent as JSON"}, status_code=415)
    return await call_next(request)


async def _refused(_: Request, error: Exception) -> JSONResponse:
    # only a refusal: a bare `ValueError` is also a defect the engine raised,
    # and stays a 500
    status = 404 if isinstance(error, Missing) else 409
    return JSONResponse({"detail": str(error)}, status_code=status)
