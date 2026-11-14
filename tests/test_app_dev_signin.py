from urllib.parse import parse_qs, urlsplit

from test_api_dev_login import browser
from test_app_signin import CHALLENGE, JSON, VERIFIER

from climb.api.apps import APP_REDIRECTS


def dev_flow(client, challenge=CHALLENGE, kind="app-dev"):
    return client.get(f"/api/auth/dev?client={kind}&code_challenge={challenge}")


def code_in(response) -> str:
    location = urlsplit(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == APP_REDIRECTS["app-dev"]
    return parse_qs(location.query)["code"][0]


def test_the_dev_login_returns_the_dev_app_to_its_own_scheme(database):
    """The dev app registers `climbancedev://`, so the release app on the same
    phone never receives its code."""
    response = dev_flow(browser(database))

    assert response.status_code == 303
    assert code_in(response)
    assert "session" not in response.cookies


def test_the_dev_app_exchanges_its_code_where_no_provider_is_configured(database):
    """The local engine offers the dev login alone, and the exchange is
    mounted all the same."""
    client = browser(database)
    code = code_in(dev_flow(client))

    exchange = {"code": code, "verifier": VERIFIER, "device": "phone-dev"}
    answer = client.post("/api/auth/app/token", json=exchange, headers=JSON)

    assert answer.status_code == 200
    bearer = {"authorization": f"Bearer {answer.json()['token']}"}
    assert client.get("/api/knowledge/snapshot", headers=bearer).status_code == 200


def test_the_dev_login_serves_the_dev_app_alone(database):
    """The release app syncs with production, so a local engine has no code
    to hand it."""
    assert dev_flow(browser(database), kind="app").status_code == 400


def test_the_dev_app_s_flow_still_answers_on_loopback_alone(database):
    assert dev_flow(browser(database, host="192.168.1.20")).status_code == 403


def test_the_dev_app_s_flow_needs_a_well_formed_challenge(database):
    assert dev_flow(browser(database), challenge="short").status_code == 400
