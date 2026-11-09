"""Signing in through Google or GitHub: `README.md` gives why the engine holds
no password. Authlib runs the round trip and checks the state, the nonce and
PKCE; this module reads who signed in."""

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, NamedTuple, Protocol, cast

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse
from joserfc.errors import JoseError
from starlette.middleware.sessions import SessionMiddleware

from algo_coach.api.context import SESSION_COOKIE, Root
from algo_coach.log import LIFETIME, Provider, invited, opened, signed_in

LOGGER = logging.getLogger(__name__)
# the page the frontend routes a refusal to
LOGIN_PAGE = "/login"


class Refusal(StrEnum):
    """Why a sign-in did not complete, as the login page reads it. A code
    rather than a sentence: a sentence names the address that was refused, and
    a URL is kept in the browser's history and in every log it passes."""

    INCOMPLETE = "incomplete"
    NO_EMAIL = "no-email"
    UNINVITED = "uninvited"


# Google signs its ID tokens under either issuer
GOOGLE_ISSUERS = ["https://accounts.google.com", "accounts.google.com"]
# Google's discovery document written out, so a sign-in fetches nothing but the
# signing keys
REGISTERED: dict[Provider, dict[str, Any]] = {
    Provider.GOOGLE: {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
        "client_kwargs": {"scope": "openid email", "code_challenge_method": "S256"},
    },
    Provider.GITHUB: {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "api_base_url": "https://api.github.com/",
        "client_kwargs": {"scope": "user:email", "code_challenge_method": "S256"},
    },
}


@dataclass(frozen=True)
class Client:
    """The id and the secret a provider issued for this engine."""

    id: str
    secret: str


@dataclass(frozen=True)
class SignIn:
    """The pages' origin a provider sends the user back to, the key the round
    trip's state is signed with, and a client per provider offered."""

    origin: str
    secret: str
    clients: Mapping[Provider, Client]

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> SignIn | None:
        """`None` where no provider has a client: the routes are then absent."""
        clients = {
            provider: Client(
                _required(environ, f"{provider.upper()}_CLIENT_ID"),
                _required(environ, f"{provider.upper()}_CLIENT_SECRET"),
            )
            for provider in Provider
            if environ.get(f"{provider.upper()}_CLIENT_ID")
        }
        if not clients:
            return None
        return cls(
            origin=_required(environ, "ALGO_COACH_ORIGIN"),
            secret=_required(environ, "ALGO_COACH_SECRET"),
            clients=clients,
        )


class Remote(Protocol):
    """The part of an Authlib client the routes call. Authlib ships no types,
    so its client is cast to this where the registry hands one out."""

    async def authorize_redirect(self, request: Request, redirect_uri: str) -> RedirectResponse: ...

    async def authorize_access_token(
        self, request: Request, **kwargs: object
    ) -> dict[str, Any]: ...

    async def get(self, url: str, *, token: dict[str, Any]) -> httpx.Response: ...


class Account(NamedTuple):
    provider_user_id: str
    # `None` where the provider verified no email, which signs nobody in
    email: str | None


def install(app: FastAPI, sign_in: SignIn, prefix: str) -> None:
    oauth = cast(Any, OAuth())
    for provider, client in sign_in.clients.items():
        oauth.register(
            provider.value, client_id=client.id, client_secret=client.secret, **REGISTERED[provider]
        )
    app.state.oauth = oauth
    app.state.providers = list(sign_in.clients)
    app.state.origin = sign_in.origin
    # the state, the nonce and the PKCE verifier, between the redirect and the
    # callback. Lax, since the callback is a navigation from the provider's site
    app.add_middleware(
        SessionMiddleware,
        secret_key=sign_in.secret,
        session_cookie="sign_in",
        max_age=600,
        same_site="lax",
        https_only=sign_in.origin.startswith("https://"),
    )
    app.include_router(router, prefix=prefix)


router = APIRouter(prefix="/auth", include_in_schema=False)


@router.get("/{provider}")
async def redirect(provider: Provider, request: Request) -> RedirectResponse:
    back = f"{request.app.state.origin}{request.url.path}/callback"
    return await _client(request, provider).authorize_redirect(request, back)


@router.get("/{provider}/callback")
async def callback(provider: Provider, request: Request, root: Root) -> RedirectResponse:
    try:
        account = await ACCOUNTS[provider](_client(request, provider), request)
    # a refused consent, a state no redirect stored, or an ID token another
    # sign-in was issued
    except (OAuthError, JoseError) as error:
        # the browser is sent back to the login, so the reason is readable
        # nowhere else
        LOGGER.warning("sign-in through %s did not complete: %s", provider, error)
        return refused(Refusal.INCOMPLETE)
    if account.email is None:
        return refused(Refusal.NO_EMAIL)
    # before anything is stored: an uninvited account leaves no user behind
    if not await run_in_threadpool(invited, root, account.email):
        return refused(Refusal.UNINVITED)
    user_id = await run_in_threadpool(
        signed_in, root, provider, account.provider_user_id, account.email
    )
    token = await run_in_threadpool(opened, root, user_id)
    return session_redirect(token, secure=request.app.state.origin.startswith("https://"))


# the callback is a navigation from the provider's site, so a refusal answers
# with the page that explains it rather than a record of it
def refused(reason: Refusal) -> RedirectResponse:
    """Back to the login page, which says what the code means."""
    return RedirectResponse(f"{LOGIN_PAGE}?refused={reason}", status_code=303)


def session_redirect(token: str, *, secure: bool) -> RedirectResponse:
    """To the pages, carrying a session opened for the user signed in."""
    response = RedirectResponse("/", status_code=303)
    # out of the pages' scripts' reach, and sent on the navigation back from the
    # provider's site, which Strict would withhold
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(LIFETIME.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return response


async def _google(client: Remote, request: Request) -> Account:
    token = await client.authorize_access_token(
        request, claims_options={"iss": {"values": GOOGLE_ISSUERS}}
    )
    claims = token["userinfo"]
    return Account(claims["sub"], claims["email"] if claims.get("email_verified") else None)


async def _github(client: Remote, request: Request) -> Account:
    token = await client.authorize_access_token(request)
    user = await client.get("user", token=token)
    user.raise_for_status()
    emails = await client.get("user/emails", token=token)
    emails.raise_for_status()
    # the primary address alone, and only once GitHub verified it
    verified = next(
        (one["email"] for one in emails.json() if one["primary"] and one["verified"]), None
    )
    return Account(str(user.json()["id"]), verified)


ACCOUNTS: dict[Provider, Callable[[Remote, Request], Awaitable[Account]]] = {
    Provider.GOOGLE: _google,
    Provider.GITHUB: _github,
}


def _client(request: Request, provider: Provider) -> Remote:
    client = request.app.state.oauth.create_client(provider.value)
    if client is None:
        raise HTTPException(404, f"no sign-in through {provider}")
    return cast(Remote, client)


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise ValueError(f"{name} is unset, and signing in needs it")
    return value
