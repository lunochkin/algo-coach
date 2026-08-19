import json
from pathlib import Path

import pytest

from algo_coach import cli
from algo_coach.cards import CardStore
from algo_coach.ingest import seed_cards

CONTENT = Path(__file__).parents[1] / "content" / "cards"


def template(slug: str = "predicate-first-true", **overrides) -> dict:
    return {
        "slug": slug,
        "title": slug,
        "trigger": "a monotone predicate over the range",
        "code": "def f(): pass",
    } | overrides


def record(slug: str = "binary-search", *, technique: str = "binary-search", **overrides) -> dict:
    return {
        "slug": slug,
        "technique": technique,
        "title": "Binary search",
        "trigger": "a sorted range and a monotone predicate",
        "brief": "## Core idea\n\nHalve the range.",
        "templates": [template()],
        "selector": {"technique": technique, "size": 5},
    } | overrides


def test_seed_mints_identity(tmp_path):
    """The author writes slugs; the engine owns every id, at both levels."""
    store = CardStore(tmp_path)
    result = seed_cards([record()], store=store)

    assert result.ingested == 1
    assert result.updated == 0
    card = store.all()[0]
    assert card.id
    assert card.slug == "binary-search"
    assert [t.id for t in card.templates] == [card.templates[0].id]
    assert card.templates[0].id
    assert card.templates[0].slug == "predicate-first-true"


def test_the_payload_cannot_supply_identity(tmp_path):
    """The seed has no field for an id, so writing one supplies nothing."""
    store = CardStore(tmp_path)
    seed_cards([record(id="forged", templates=[template(id="forged-template")])], store=store)

    card = store.all()[0]
    assert card.id != "forged"
    assert card.templates[0].id != "forged-template"


def test_reseeding_a_slug_refreshes_and_keeps_the_id(tmp_path):
    """A card run references the id, so re-seeding never moves it."""
    store = CardStore(tmp_path)
    seed_cards([record()], store=store)
    minted = store.all()[0].id

    result = seed_cards([record(title="Binary search, revised")], store=store)

    assert result.ingested == 0
    assert result.updated == 1
    assert len(store.all()) == 1
    assert store.get(minted).title == "Binary search, revised"


def test_a_template_keeps_its_id_across_a_reseed(tmp_path):
    """Recall is per template and keys to its id, so the slug is what a
    re-seed matches on; a template the author added gets a new one."""
    store = CardStore(tmp_path)
    seed_cards([record()], store=store)
    before = {t.slug: t.id for t in store.all()[0].templates}

    seed_cards(
        [record(templates=[template(title="renamed"), template("answer-space")])],
        store=store,
    )

    after = {t.slug: t.id for t in store.all()[0].templates}
    assert after["predicate-first-true"] == before["predicate-first-true"]
    assert after["answer-space"] not in before.values()
    assert store.all()[0].templates[0].title == "renamed"


def test_a_new_slug_is_a_new_card(tmp_path):
    """Renaming is a title change: the runs and the recall history stay with
    the card whose slug they were written against."""
    store = CardStore(tmp_path)
    seed_cards([record()], store=store)
    result = seed_cards([record("binary-search-advanced")], store=store)

    assert result.ingested == 1
    assert result.updated == 0
    assert sorted(card.slug for card in store.all()) == [
        "binary-search",
        "binary-search-advanced",
    ]


@pytest.mark.parametrize("field", ["technique", "selector"])
def test_an_unknown_technique_is_rejected(tmp_path, field):
    """Membership is checked on the write path — here, and on the selector a
    ladder draws by, where an unknown code would resolve to nothing and say
    nothing."""
    store = CardStore(tmp_path)
    overrides = (
        {"technique": "sliding-windows"}
        if field == "technique"
        else {"selector": {"technique": "sliding-windows", "size": 5}}
    )
    result = seed_cards([record(**overrides)], store=store)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert store.all() == []


def test_an_invalid_card_does_not_stop_the_batch(tmp_path):
    """Per record, by index, as at every other boundary."""
    store = CardStore(tmp_path)
    result = seed_cards(
        [
            record("binary-search"),
            {"slug": "half-written"},
            record("union-find", technique="union-find"),
        ],
        store=store,
    )

    assert result.ingested == 2
    assert [r.index for r in result.rejected] == [1]
    assert sorted(card.slug for card in store.all()) == ["binary-search", "union-find"]


def test_a_card_rejected_by_its_own_validator(tmp_path):
    """Two templates sharing a slug leave a re-seed with no rule for which
    minted id to keep."""
    store = CardStore(tmp_path)
    result = seed_cards([record(templates=[template(), template()])], store=store)

    assert [r.index for r in result.rejected] == [0]


def test_empty_batch(tmp_path):
    result = seed_cards([], store=CardStore(tmp_path))

    assert result.ingested == 0
    assert result.updated == 0
    assert result.rejected == []


def test_seed_cards_command_over_a_directory(tmp_path, monkeypatch, capsys):
    source = tmp_path / "authored"
    source.mkdir()
    (source / "binary-search.json").write_text(json.dumps(record()))
    (source / "union-find.json").write_text(
        json.dumps(record("union-find", technique="union-find"))
    )
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "seed", "cards", str(source)])

    cli.main()

    assert len(CardStore(tmp_path / "data").all()) == 2
    assert json.loads(capsys.readouterr().out)["ingested"] == 2


def test_seed_cards_command_over_one_file(tmp_path, monkeypatch, capsys):
    source = tmp_path / "binary-search.json"
    source.write_text(json.dumps(record()))
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "seed", "cards", str(source)])

    cli.main()

    assert len(CardStore(tmp_path / "data").all()) == 1


def test_a_rejected_card_exits_nonzero(tmp_path, monkeypatch, capsys):
    source = tmp_path / "broken.json"
    source.write_text(json.dumps({"slug": "half-written"}))
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "seed", "cards", str(source)])

    with pytest.raises(SystemExit) as exit:
        cli.main()

    assert exit.value.code == 1
    assert json.loads(capsys.readouterr().out)["rejected"]


def test_a_file_that_is_not_json_never_reaches_the_engine(tmp_path, monkeypatch, capsys):
    """Corrupt transport, not an invalid card: it cannot come back as a
    rejection, since nothing validated it."""
    source = tmp_path / "broken.json"
    source.write_text("{")
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "seed", "cards", str(source)])

    with pytest.raises(SystemExit) as exit:
        cli.main()

    assert exit.value.code == 2
    assert "seed:" in capsys.readouterr().err


def test_the_authored_cards_seed(tmp_path):
    """The content in this repo is what the path exists to load, so it is
    seeded rather than described."""
    store = CardStore(tmp_path)
    result = seed_cards(
        [json.loads(path.read_text()) for path in sorted(CONTENT.glob("*.json"))], store=store
    )

    assert result.rejected == []
    assert result.ingested == len(list(CONTENT.glob("*.json")))
    assert all(card.templates for card in store.all())
