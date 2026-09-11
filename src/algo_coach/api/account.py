"""The routes the pages sign in and out through: the sign-ins the engine
offers, and ending the session a browser carries. Neither needs a session."""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from algo_coach.api.context import SESSION_COOKIE, Root
from algo_coach.log import Provider, revoked

router = APIRouter()


class Offered(BaseModel):
    """What the login page offers."""

    providers: list[Provider]
    # the user the dev login signs in as, where it is enabled
    dev_login: str | None


@router.get("/sign-in")
def offered(request: Request) -> Offered:
    return Offered(providers=request.app.state.providers, dev_login=request.app.state.dev_user)


@router.delete("/session", status_code=204)
def signed_out(request: Request, root: Root) -> Response:
    # revoked rather than only forgotten: a copy of the cookie signs nobody in
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        revoked(root, token)
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")
    return response
