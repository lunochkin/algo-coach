import json

import pytest

from algo_coach import cli
from algo_coach.ingest import ingest_problems
from algo_coach.problems import ProblemStore
from algo_coach.schema import ProblemDifficulty, ProblemOwner


def record(external_id: str = "e1", **overrides) -> dict:
    return {
        "external_id": external_id,
        "title": "Two Sum",
        "title_slug": "two-sum",
        "statement": "Given an array, return ...",
    } | overrides


def test_ingest_stamps_provenance(tmp_path):
    store = ProblemStore(tmp_path)
    result = ingest_problems([record()], user_id="u1", store=store)

    assert result.ingested == 1
    assert result.updated == 0
    problem = store.all()[0]
    assert problem.owner is ProblemOwner.USER
    assert problem.user_id == "u1"
    assert problem.external_id == "e1"
    assert problem.id


def test_payload_cannot_supply_owner_or_identity(tmp_path):
    store = ProblemStore(tmp_path)
    ingest_problems(
        [record(id="forged", user_id="someone-else", owner="product")],
        user_id="u1",
        store=store,
    )

    problem = store.all()[0]
    assert problem.owner is ProblemOwner.USER
    assert problem.user_id == "u1"
    assert problem.id != "forged"


def test_client_supplied_techniques_are_dropped(tmp_path):
    """Codes are engine-derived; a client only gets to send platform tags."""
    store = ProblemStore(tmp_path)
    ingest_problems(
        [record(techniques=["backtracking"], source_tags=["Dynamic Programming"])],
        user_id="u1",
        store=store,
    )

    problem = store.all()[0]
    assert problem.techniques == ["dynamic-programming"]
    assert problem.source_tags == ["Dynamic Programming"]


def test_unmapped_tags_survive_without_a_code(tmp_path):
    store = ProblemStore(tmp_path)
    ingest_problems([record(source_tags=["Simulation"])], user_id="u1", store=store)

    problem = store.all()[0]
    assert problem.techniques == []
    assert problem.source_tags == ["Simulation"]


def test_re_push_re_derives_techniques(tmp_path):
    """Raw tags are the truth; codes are a view over them, recomputed."""
    store = ProblemStore(tmp_path)
    ingest_problems([record(source_tags=["Greedy"])], user_id="u1", store=store)
    ingest_problems([record(source_tags=["Trie"])], user_id="u1", store=store)

    assert store.all()[0].techniques == ["trie"]


def test_statement_lands_verbatim(tmp_path):
    store = ProblemStore(tmp_path)
    ingest_problems([record(statement="Given an array...")], user_id="u1", store=store)

    assert store.all()[0].statement == "Given an array..."


@pytest.mark.parametrize("statement", [None, ""])
def test_a_problem_without_a_statement_is_rejected(tmp_path, statement):
    """Matching reads the statement, so a corpus missing one is silent rather
    than short. Rejecting is per record, and the push is re-runnable."""
    store = ProblemStore(tmp_path)
    payload = record()
    if statement is None:
        del payload["statement"]
    else:
        payload["statement"] = statement

    result = ingest_problems([payload], user_id="u1", store=store)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert store.all() == []


def test_re_push_updates_in_place(tmp_path):
    store = ProblemStore(tmp_path)
    ingest_problems([record(title="Two Sum")], user_id="u1", store=store)
    result = ingest_problems(
        [record(title="Two Sum II", difficulty="hard", statement="restated")],
        user_id="u1",
        store=store,
    )

    assert result.ingested == 0
    assert result.updated == 1
    assert len(store.all()) == 1
    problem = store.all()[0]
    assert problem.title == "Two Sum II"
    assert problem.difficulty is ProblemDifficulty.HARD
    assert problem.statement == "restated"


def test_re_push_keeps_identity(tmp_path):
    """Attempts already reference the engine-minted id; it cannot move."""
    store = ProblemStore(tmp_path)
    ingest_problems([record()], user_id="u1", store=store)
    original = store.all()[0].id

    ingest_problems([record(title="renamed")], user_id="u1", store=store)

    assert store.all()[0].id == original


def test_push_identity_is_scoped_to_the_user(tmp_path):
    store = ProblemStore(tmp_path)
    ingest_problems([record("e1")], user_id="u1", store=store)
    result = ingest_problems([record("e1")], user_id="u2", store=store)

    assert result.ingested == 1
    assert result.updated == 0
    assert len(store.all()) == 2


def test_external_id_is_required(tmp_path):
    store = ProblemStore(tmp_path)
    payload = record()
    del payload["external_id"]

    result = ingest_problems([payload], user_id="u1", store=store)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert store.all() == []


def test_malformed_record_does_not_stop_the_batch(tmp_path):
    store = ProblemStore(tmp_path)
    result = ingest_problems(
        [record("e1"), {"external_id": "e2"}, record("e3")], user_id="u1", store=store
    )

    assert result.ingested == 2
    assert [r.index for r in result.rejected] == [1]
    assert sorted(p.external_id for p in store.all()) == ["e1", "e3"]


def test_empty_batch(tmp_path):
    result = ingest_problems([], user_id="u1", store=ProblemStore(tmp_path))

    assert result.ingested == 0
    assert result.updated == 0
    assert result.rejected == []


def test_push_problems_command(tmp_path, monkeypatch, capsys):
    source = tmp_path / "problems.jsonl"
    source.write_text(json.dumps(record("e1")) + "\n" + json.dumps(record("e2")) + "\n")
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "push", "problems", str(source), "--user", "u1"])

    cli.main()

    assert len(ProblemStore(tmp_path / "data").all()) == 2
    assert json.loads(capsys.readouterr().out)["ingested"] == 2


def test_push_rejects_unknown_kind(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["algo-coach", "push", "diagnoses", "f.jsonl"])

    with pytest.raises(SystemExit):
        cli.main()
