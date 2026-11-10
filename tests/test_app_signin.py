import base64
import hashlib
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import select, update
from test_api_signin import browser, google_returns

from algo_coach.api.apps import APP_REDIRECTS
from algo_coach.log import Provider, hashed, invite
from algo_coach.log.table import app_codes, app_tokens

VERIFIER = "v" * 43 + "-the-app-s-own-secret"
CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()
)
JSON = {"content-type": "application/json"}


def started(client, challenge=CHALLENGE) -> dict[str, str]:
    response = client.get(f"/api/auth/{Provider.GOOGLE}?client=app&code_challenge={challenge}")
    assert response.status_code == 302
    query = parse_qs(urlsplit(response.headers["location"]).query)
    return {key: value for key, (value,) in query.items()}


def returned(database, monkeypatch, *, invited=True):
    """The app's round trip through Google, up to the redirect back to it."""
    if invited:
        invite(database, "solver@example.com")
    client = browser(database)
    sent = started(client)
    google_returns(monkeypatch, client, nonce=sent["nonce"])
    return client, client.get(f"/api/auth/google/callback?code=abc&state={sent['state']}")


def code_in(response) -> str:
    location = urlsplit(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == APP_REDIRECTS["app"]
    return parse_qs(location.query)["code"][0]


def exchanged(client, code, verifier=VERIFIER):
    body = {"code": code, "verifier": verifier, "device": "phone"}
    return client.post("/api/auth/app/token", json=body, headers=JSON)


def signed_in_app(database, monkeypatch):
    client, response = returned(database, monkeypatch)
    token = exchanged(client, code_in(response)).json()["token"]
    return client, token


def test_the_callback_returns_to_the_app_with_a_code_and_no_cookie(database, monkeypatch):
    """The app cannot carry the pages' cookie, so the flow ends in a code it
    exchanges: `README.md`."""
    _, response = returned(database, monkeypatch)

    assert response.status_code == 303
    assert code_in(response)
    assert "session" not in response.cookies


def test_the_code_and_the_verifier_exchange_for_a_token(database, monkeypatch):
    client, response = returned(database, monkeypatch)

    answer = exchanged(client, code_in(response))

    assert answer.status_code == 200
    with database.connect() as conn:
        (stored,) = conn.execute(select(app_tokens.c.id, app_tokens.c.device)).all()
    assert tuple(stored) == (hashed(answer.json()["token"]), "phone")


def test_the_token_names_its_user(database, monkeypatch):
    """The app keys its copy of the log to the user: `knowledge.md`."""
    client, response = returned(database, monkeypatch)

    issued = exchanged(client, code_in(response)).json()

    with database.connect() as conn:
        (owner,) = conn.execute(select(app_tokens.c.user_id)).scalars().all()
    assert issued["user_id"] == owner


def test_a_code_without_its_verifier_signs_no_app_in(database, monkeypatch):
    """Another app claiming the scheme receives the code, and the verifier is
    what it lacks."""
    client, response = returned(database, monkeypatch)

    assert exchanged(client, code_in(response), verifier="w" * 43).status_code == 400


def test_a_code_is_exchanged_once(database, monkeypatch):
    client, response = returned(database, monkeypatch)
    code = code_in(response)
    exchanged(client, code)

    assert exchanged(client, code).status_code == 400


def test_an_expired_code_signs_no_app_in(database, monkeypatch):
    client, response = returned(database, monkeypatch)
    with database.begin() as conn:
        issued_at = datetime.now(UTC) - timedelta(minutes=6)
        conn.execute(
            update(app_codes).values(
                created_at=issued_at, expires_at=issued_at + timedelta(minutes=5)
            )
        )

    assert exchanged(client, code_in(response)).status_code == 400


def test_the_code_is_stored_as_its_hash(database, monkeypatch):
    _, response = returned(database, monkeypatch)

    with database.connect() as conn:
        assert conn.execute(select(app_codes.c.id)).scalar_one() == hashed(code_in(response))


def test_an_uninvited_email_returns_to_the_app_refused(database, monkeypatch):
    _, response = returned(database, monkeypatch, invited=False)

    location = urlsplit(response.headers["location"])
    assert parse_qs(location.query) == {"refused": ["uninvited"]}


@pytest.mark.parametrize("challenge", ["", "short", "x" * 43 + "!"])
def test_an_app_flow_needs_a_well_formed_challenge(database, challenge):
    client = browser(database)

    response = client.get(f"/api/auth/{Provider.GOOGLE}?client=app&code_challenge={challenge}")

    assert response.status_code == 400


def test_the_token_reads_the_knowledge_endpoints(database, monkeypatch):
    client, token = signed_in_app(database, monkeypatch)

    response = client.get("/api/knowledge/snapshot", headers={"authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_the_token_reaches_nothing_else_of_the_account(database, monkeypatch):
    """A token taken from a lost phone reads and writes the knowledge log, and
    nothing else."""
    client, token = signed_in_app(database, monkeypatch)

    assert client.get("/api/board", headers={"authorization": f"Bearer {token}"}).status_code == 401


def test_signing_out_in_the_app_revokes_its_token(database, monkeypatch):
    client, token = signed_in_app(database, monkeypatch)
    bearer = {"authorization": f"Bearer {token}", **JSON}

    assert client.post("/api/auth/app/signout", headers=bearer).status_code == 204
    assert client.get("/api/knowledge/snapshot", headers=bearer).status_code == 401


def test_a_token_unused_for_ninety_days_expires(database, monkeypatch):
    client, token = signed_in_app(database, monkeypatch)
    with database.begin() as conn:
        long_ago = datetime.now(UTC) - timedelta(days=91)
        conn.execute(update(app_tokens).values(last_used_at=long_ago))

    response = client.get("/api/knowledge/snapshot", headers={"authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_each_use_extends_the_token(database, monkeypatch):
    """The app works offline for days, so the lifetime counts from the last
    use: `README.md`."""
    client, token = signed_in_app(database, monkeypatch)
    with database.begin() as conn:
        conn.execute(update(app_tokens).values(last_used_at=datetime.now(UTC) - timedelta(days=80)))

    client.get("/api/knowledge/snapshot", headers={"authorization": f"Bearer {token}"})

    with database.connect() as conn:
        used = conn.execute(select(app_tokens.c.last_used_at)).scalar_one()
    assert datetime.now(UTC) - used < timedelta(minutes=1)


def test_a_provider_returns_the_dev_app_to_its_own_scheme(database, monkeypatch):
    invite(database, "solver@example.com")
    client = browser(database)
    response = client.get(f"/api/auth/{Provider.GOOGLE}?client=app-dev&code_challenge={CHALLENGE}")
    sent = {k: v for k, (v,) in parse_qs(urlsplit(response.headers["location"]).query).items()}
    google_returns(monkeypatch, client, nonce=sent["nonce"])

    back = client.get(f"/api/auth/google/callback?code=abc&state={sent['state']}")

    assert back.headers["location"].startswith(APP_REDIRECTS["app-dev"] + "?code=")


def test_an_unknown_client_is_refused(database):
    started = f"/api/auth/{Provider.GOOGLE}?client=web&code_challenge={CHALLENGE}"
    response = browser(database).get(started)

    assert response.status_code == 400
