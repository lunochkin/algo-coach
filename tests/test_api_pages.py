import pytest
from fastapi.testclient import TestClient

from algo_coach.api import create_app
from algo_coach.storage import Database

INDEX = "<!doctype html><title>algo-coach</title>"


@pytest.fixture
def client(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(INDEX)
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("not a page")
    return TestClient(create_app(Database(), dev_login="local", pages=dist))


def test_a_file_the_pages_carry_is_served(client):
    """The built assets reach the browser from the API's own origin."""
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert response.text == "console.log(1)"


def test_the_root_is_the_app(client):
    """The page a browser opens first."""
    assert client.get("/").text == INDEX


def test_a_path_naming_no_file_is_the_app(client):
    """The frontend routes by URL, so a reload of any page reaches the app."""
    response = client.get("/problems/p1/sitting")
    assert response.status_code == 200
    assert response.text == INDEX


def test_a_route_under_the_prefix_still_answers(client):
    """The mount at the root answers only what the API's routes left."""
    assert client.get("/api/sign-in").json() == {"providers": [], "dev_login": "local"}


def test_a_path_under_the_prefix_naming_no_route_is_a_miss(client):
    """A mistyped API path is a 404 the pages would otherwise hide."""
    assert client.get("/api/nothing-here").status_code == 404


def test_a_path_climbing_out_of_the_pages_reads_nothing_there(client):
    """A file beside the built pages stays unread whatever the path says."""
    assert client.get("/%2e%2e/secret.txt").text == INDEX
