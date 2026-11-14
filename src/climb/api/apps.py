"""The native app's side of signing in, whichever flow issued its code: a
provider's, or the dev login's on a local engine. `README.md` gives the
rules."""

import re
from enum import StrEnum

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from climb.api.context import Root
from climb.log import app_revoked, exchanged

# where each app's sign-in returns to, by the client the flow names. Constants,
# so no request can name a redirect of its own. The dev app's scheme is its own,
# so the release app on the same phone never receives the dev app's code
APP_REDIRECTS = {
    "app": "climbance://signed-in",
    "app-dev": "climbancedev://signed-in",
}
# a PKCE S256 challenge: 43 characters of unpadded base64url
CHALLENGE = re.compile(r"[A-Za-z0-9_-]{43}")

router = APIRouter(prefix="/auth/app", include_in_schema=False)


def challenge_of(client: str, challenge: str) -> str:
    """The challenge an app's flow sent, refused where the client or the
    challenge is not one the engine knows."""
    if client not in APP_REDIRECTS:
        raise HTTPException(400, "an app's sign-in names a known client")
    if not CHALLENGE.fullmatch(challenge):
        raise HTTPException(400, "an app's sign-in sends a PKCE S256 challenge")
    return challenge


def refused_in_app(client: str, reason: StrEnum) -> RedirectResponse:
    return RedirectResponse(f"{APP_REDIRECTS[client]}?refused={reason}", status_code=303)


class Exchange(BaseModel):
    code: str = Field(min_length=1)
    verifier: str = Field(min_length=43, max_length=128)
    device: str = Field(min_length=1)


class Issued(BaseModel):
    token: str
    # the user the app keys its copy of the log to: `knowledge.md`
    user_id: str


@router.post("/token")
def token(exchange: Exchange, root: Root) -> Issued:
    found = exchanged(root, exchange.code, exchange.verifier, exchange.device)
    if found is None:
        raise HTTPException(400, "the code is spent, expired, or not this app's")
    return Issued(token=found[0], user_id=found[1])


@router.post("/signout", status_code=204)
def signout(request: Request, root: Root) -> None:
    scheme, _, bearer = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and bearer:
        app_revoked(root, bearer)
