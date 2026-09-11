"""Signing in with no provider, as the user `ALGO_COACH_DEV_LOGIN` names, for
local work: `README.md` gives the guards that keep it off a deployed engine."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse

from algo_coach.api.context import Root
from algo_coach.api.signin import session_redirect
from algo_coach.log import named, opened

# the addresses only a request from this machine arrives at
LOOPBACK = {"127.0.0.1", "::1"}

router = APIRouter(prefix="/auth", include_in_schema=False)


@router.get("/dev")
async def dev_login(request: Request, root: Root) -> RedirectResponse:
    # the address the request arrived at, which another machine's request never
    # is. Checked per request: the app is built before any address is bound
    server = request.scope.get("server")
    if server is None or server[0] not in LOOPBACK:
        raise HTTPException(403, "the dev login answers on 127.0.0.1 alone")
    user_id = request.app.state.dev_user
    await run_in_threadpool(named, root, user_id)
    token = await run_in_threadpool(opened, root, user_id)
    return session_redirect(token, secure=False)
