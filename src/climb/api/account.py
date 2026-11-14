"""The routes the pages sign in and out through: the sign-ins the engine
offers, who the session signs in as, and ending the session a browser
carries."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from climb.api.context import SESSION_COOKIE, Root, UserId, bearer_of
from climb.log import (
    DeviceKind,
    Provider,
    SignedInDevice,
    device_revoked,
    email_of,
    revoked,
    signed_in_devices,
)

router = APIRouter()


class Offered(BaseModel):
    """What the login page offers."""

    providers: list[Provider]
    # the user the dev login signs in as, where it is enabled
    dev_login: str | None


@router.get("/sign-in")
def offered(request: Request) -> Offered:
    return Offered(providers=request.app.state.providers, dev_login=request.app.state.dev_user)


class Me(BaseModel):
    """Who the session signs in as. The engine mints the id, and the address is
    the provider's, so a user reached by the dev login carries none."""

    user_id: str
    email: str | None


@router.get("/me")
def me(root: Root, user_id: UserId) -> Me:
    return Me(user_id=user_id, email=email_of(root, user_id))


@router.delete("/session", status_code=204)
def signed_out(request: Request, root: Root) -> Response:
    # revoked rather than only forgotten: a copy of the cookie signs nobody in
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        revoked(root, token)
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")
    return response


@router.get("/devices")
def devices(request: Request, root: Root, user_id: UserId) -> list[SignedInDevice]:
    """Every browser and app signed in as the user, the one asking marked."""
    return signed_in_devices(
        root,
        user_id,
        app_token=bearer_of(request),
        session_token=request.cookies.get(SESSION_COOKIE),
    )


@router.delete("/devices/{kind}/{device_id}", status_code=204)
def revoke_device(kind: DeviceKind, device_id: str, root: Root, user_id: UserId) -> Response:
    # a lost phone or a forgotten browser is cut off here, from any other client
    if not device_revoked(root, user_id, kind, device_id):
        raise HTTPException(404, "no device of yours carries this id")
    return Response(status_code=204)
