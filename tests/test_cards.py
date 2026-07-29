import json

import pytest
from pydantic import ValidationError

from algo_coach.cards import Card, CardStore


def test_create_card_writes_one_file_per_card(tmp_path):
    store = CardStore(tmp_path)
    store.create_card(Card(name="monotonic-stack"))

    assert (tmp_path / "cards" / "monotonic-stack.json").exists()


def test_create_card_roundtrips(tmp_path):
    store = CardStore(tmp_path)
    card = Card(name="backtracking")
    store.create_card(card)

    written = (tmp_path / "cards" / "backtracking.json").read_text()
    assert Card.model_validate_json(written) == card


def test_created_file_is_hand_editable(tmp_path):
    """Indented and newline-terminated: these files get edited and diffed."""
    store = CardStore(tmp_path)
    store.create_card(Card(name="two-pointers"))

    written = (tmp_path / "cards" / "two-pointers.json").read_text()
    assert written.endswith("\n")
    assert "\n" in written.strip()  # multi-line => indented
    assert json.loads(written) == {"name": "two-pointers"}


def test_create_card_makes_missing_dirs(tmp_path):
    store = CardStore(tmp_path / "nested" / "root")
    store.create_card(Card(name="union-find"))

    assert (tmp_path / "nested" / "root" / "cards" / "union-find.json").exists()


def test_create_card_rejects_duplicate(tmp_path):
    store = CardStore(tmp_path)
    store.create_card(Card(name="binary-search"))

    with pytest.raises(FileExistsError):
        store.create_card(Card(name="binary-search"))


def test_create_card_does_not_clobber_on_duplicate(tmp_path):
    store = CardStore(tmp_path)
    store.create_card(Card(name="dijkstra"))
    path = tmp_path / "cards" / "dijkstra.json"
    path.write_text('{"name": "dijkstra", "edited": true}\n')

    with pytest.raises(FileExistsError):
        store.create_card(Card(name="dijkstra"))

    assert json.loads(path.read_text())["edited"] is True


@pytest.mark.parametrize("name", ["", "  ", "\t", "../evil", "a/b", "Foo", "-leading-dash"])
def test_card_name_must_be_a_safe_slug(name):
    with pytest.raises(ValidationError):
        Card(name=name)


@pytest.mark.parametrize("name", ["monotonic-stack", "backtracking"])
def test_card_name_accepts_slug(name):
    assert Card(name=name).name == name
