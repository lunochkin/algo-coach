import json
from pathlib import Path

from algo_coach.api.__main__ import app

COMMITTED = Path(__file__).resolve().parent.parent / "web" / "src" / "api" / "openapi.json"


def test_the_page_is_typed_against_the_api_as_it_stands():
    """The page's request and response types are generated from this schema,
    so a route changed without `just types` leaves the page typed against an
    API that no longer exists."""
    assert json.loads(COMMITTED.read_text()) == json.loads(json.dumps(app().openapi()))
