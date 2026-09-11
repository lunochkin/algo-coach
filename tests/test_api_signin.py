import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from joserfc import jwt
from joserfc.jwk import RSAKey
from sqlalchemy import select

from algo_coach.api import create_app
from algo_coach.api.signin import Client, SignIn
from algo_coach.log import Provider
from algo_coach.log.table import identities
from algo_coach.storage import Database

ORIGIN = "http://localhost:5173"
CLIENTS = {
    Provider.GOOGLE: Client("google-id", "google-secret"),
    Provider.GITHUB: Client("github-id", "github-secret"),
}
# Google's signing key, stood in for by one made here, so the ID token a test
# returns is checked as a real one is
KEY = RSAKey.generate_key(2048, parameters={"kid": "google-key"})


def browser(root, clients=CLIENTS) -> TestClient:
    app = create_app(root, user_id="local", sign_in=SignIn(ORIGIN, "a-test-key", clients))
    return TestClient(app, follow_redirects=False)


def remote(client: TestClient, provider: Provider):
    return client.app.state.oauth.create_client(provider.value)


def redirected(client: TestClient, provider: Provider) -> dict[str, str]:
    """The query the sign-in sent the user to the provider with."""
    response = client.get(f"/api/auth/{provider}")
    assert response.status_code == 302
    return {
        key: value
        for key, (value,) in parse_qs(urlsplit(response.headers["location"]).query).items()
    }


def linked(database) -> list[tuple]:
    with database.connect() as conn:
        rows = conn.execute(
            select(identities.c.provider, identities.c.provider_user_id, identities.c.email)
        )
        return [tuple(row) for row in rows]


def test_a_sign_in_sends_the_user_to_google_with_a_state_a_nonce_and_pkce():
    """Authlib checks all three at the callback, and a redirect missing one is
    a round trip nothing checks."""
    response = browser(Database()).get("/api/auth/google")

    assert response.headers["location"].startswith("https://accounts.google.com/")
    sent = redirected(browser(Database()), Provider.GOOGLE)
    assert sent["client_id"] == "google-id"
    assert sent["redirect_uri"] == f"{ORIGIN}/api/auth/google/callback"
    assert sent["scope"] == "openid email"
    assert sent["code_challenge_method"] == "S256"
    assert {"state", "nonce", "code_challenge"} <= set(sent)


def test_github_is_sent_pkce_and_asked_for_the_account_s_emails():
    """GitHub is no OpenID provider, so no nonce: its emails are read from its
    API, which the scope opens."""
    sent = redirected(browser(Database()), Provider.GITHUB)

    assert sent["redirect_uri"] == f"{ORIGIN}/api/auth/github/callback"
    assert sent["scope"] == "user:email"
    assert "code_challenge" in sent and "nonce" not in sent


def test_a_provider_with_no_client_offers_no_sign_in():
    client = browser(Database(), {Provider.GOOGLE: CLIENTS[Provider.GOOGLE]})

    assert client.get("/api/auth/github").status_code == 404


def test_the_routes_are_absent_where_no_provider_has_a_client():
    client = TestClient(create_app(Database(), user_id="local"), follow_redirects=False)

    assert client.get("/api/auth/google").status_code == 404


def test_a_callback_no_sign_in_started_signs_nobody_in():
    """A callback carrying a state this browser was never given is the forged
    request the state exists to refuse."""
    response = browser(Database()).get("/api/auth/github/callback?code=abc&state=forged")

    assert response.status_code == 400
    assert "mismatching_state" in response.json()["detail"]


def test_a_refused_consent_signs_nobody_in():
    response = browser(Database()).get("/api/auth/google/callback?error=access_denied")

    assert response.status_code == 400
    assert "access_denied" in response.json()["detail"]


def google_returns(monkeypatch, client, **claims):
    """Google's token endpoint answering with an ID token signed by `KEY`."""
    google = remote(client, Provider.GOOGLE)
    google.server_metadata["jwks"] = {"keys": [KEY.as_dict(private=False)]}

    async def fetched(redirect_uri=None, **params):
        now = int(time.time())
        issued = {
            "iss": "https://accounts.google.com",
            "aud": "google-id",
            "sub": "108234",
            "email": "Solver@Example.com",
            "email_verified": True,
            "iat": now,
            "exp": now + 600,
        } | claims
        signed = jwt.encode({"alg": "RS256", "kid": "google-key"}, issued, KEY)
        return {"access_token": "a-token", "token_type": "Bearer", "id_token": signed}

    monkeypatch.setattr(google, "fetch_access_token", fetched)


def test_google_signs_in_the_account_behind_a_verified_email(database, monkeypatch):
    client = browser(database)
    nonce = redirected(client, Provider.GOOGLE)
    google_returns(monkeypatch, client, nonce=nonce["nonce"])

    response = client.get(f"/api/auth/google/callback?code=abc&state={nonce['state']}")

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert linked(database) == [(Provider.GOOGLE, "108234", "solver@example.com")]


def test_an_id_token_issued_to_another_sign_in_signs_nobody_in(database, monkeypatch):
    """The nonce ties the token to the redirect this browser made, so a token
    replayed from another sign-in is refused."""
    client = browser(database)
    sent = redirected(client, Provider.GOOGLE)
    google_returns(monkeypatch, client, nonce="another-sign-in")

    response = client.get(f"/api/auth/google/callback?code=abc&state={sent['state']}")

    assert response.status_code == 400
    assert "nonce" in response.json()["detail"]
    assert linked(database) == []


def test_an_unverified_google_email_signs_nobody_in(database, monkeypatch):
    """An address the provider never verified would join the log of whoever
    holds it: `README.md`."""
    client = browser(database)
    sent = redirected(client, Provider.GOOGLE)
    google_returns(monkeypatch, client, nonce=sent["nonce"], email_verified=False)

    response = client.get(f"/api/auth/google/callback?code=abc&state={sent['state']}")

    assert response.status_code == 403
    assert linked(database) == []


def github_returns(monkeypatch, client, emails: list[dict]) -> list[dict]:
    """GitHub's token endpoint and API, answering as they do. Returns what the
    token request was sent."""
    github = remote(client, Provider.GITHUB)
    sent: list[dict] = []

    async def fetched(redirect_uri=None, **params):
        sent.append(params | {"redirect_uri": redirect_uri})
        return {"access_token": "a-token", "token_type": "bearer"}

    async def got(url, token=None, **_):
        body = {"user": {"id": 583231, "login": "solver"}, "user/emails": emails}[url]
        return httpx.Response(200, json=body, request=httpx.Request("GET", url))

    monkeypatch.setattr(github, "fetch_access_token", fetched)
    monkeypatch.setattr(github, "get", got)
    return sent


def test_github_signs_in_the_account_behind_its_verified_primary_email(database, monkeypatch):
    client = browser(database)
    started = redirected(client, Provider.GITHUB)
    sent = github_returns(
        monkeypatch,
        client,
        [
            {"email": "old@example.com", "primary": False, "verified": True},
            {"email": "solver@example.com", "primary": True, "verified": True},
        ],
    )

    response = client.get(f"/api/auth/github/callback?code=abc&state={started['state']}")

    assert response.status_code == 303
    assert linked(database) == [(Provider.GITHUB, "583231", "solver@example.com")]
    # the verifier the redirect's challenge was made from, sent with the code
    (token_request,) = sent
    assert token_request["code"] == "abc" and token_request["code_verifier"]
    assert token_request["redirect_uri"] == f"{ORIGIN}/api/auth/github/callback"


def test_an_unverified_github_primary_email_signs_nobody_in(database, monkeypatch):
    """The primary address alone is read: another verified one may be an old
    address its owner no longer holds."""
    client = browser(database)
    started = redirected(client, Provider.GITHUB)
    github_returns(
        monkeypatch,
        client,
        [
            {"email": "solver@example.com", "primary": True, "verified": False},
            {"email": "old@example.com", "primary": False, "verified": True},
        ],
    )

    response = client.get(f"/api/auth/github/callback?code=abc&state={started['state']}")

    assert response.status_code == 403
    assert linked(database) == []


def test_sign_in_is_configured_from_the_environment():
    environ = {
        "GITHUB_CLIENT_ID": "github-id",
        "GITHUB_CLIENT_SECRET": "github-secret",
        "ALGO_COACH_ORIGIN": ORIGIN,
        "ALGO_COACH_SECRET": "a-test-key",
    }

    configured = SignIn.from_environ(environ)

    assert configured == SignIn(ORIGIN, "a-test-key", {Provider.GITHUB: CLIENTS[Provider.GITHUB]})
    assert SignIn.from_environ({}) is None


def test_a_provider_configured_without_the_origin_is_refused_at_start():
    """Found when the app is built, not at the first sign-in."""
    with pytest.raises(ValueError, match="ALGO_COACH_ORIGIN"):
        SignIn.from_environ({"GOOGLE_CLIENT_ID": "google-id", "GOOGLE_CLIENT_SECRET": "s"})
