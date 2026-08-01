import json
from datetime import UTC, datetime

import pytest

from algo_coach.ingest import ingest_attempts
from algo_coach.log import AttemptLog


def record(external_id: str = "e1", **overrides) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "external_id": external_id,
        "problem_id": "p1",
        "started_at": now,
        "finished_at": now,
        "code": "def f(): pass",
        "solved": True,
        "time_to_solve_sec": 900.0,
    } | overrides


def test_valid_record_is_appended(tmp_path):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([record()], user_id="u1", log=log)

    assert result.ingested == 1
    assert result.duplicates == 0
    assert result.rejected == []
    assert [a.external_id for a in log.attempts()] == ["e1"]


def test_identity_comes_from_the_adapter(tmp_path):
    log = AttemptLog(tmp_path)
    ingest_attempts([record()], user_id="u1", log=log)

    assert log.attempts()[0].user_id == "u1"


def test_payload_cannot_supply_identity(tmp_path):
    """A client that sends its own id or user_id has both overwritten."""
    log = AttemptLog(tmp_path)
    ingest_attempts(
        [record(id="forged", user_id="someone-else")], user_id="u1", log=log
    )

    attempt = log.attempts()[0]
    assert attempt.user_id == "u1"
    assert attempt.id != "forged"


def test_engine_mints_distinct_ids(tmp_path):
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1"), record("e2")], user_id="u1", log=log)

    ids = [a.id for a in log.attempts()]
    assert len(set(ids)) == 2


def test_re_push_is_a_no_op(tmp_path):
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1")], user_id="u1", log=log)
    result = ingest_attempts([record("e1")], user_id="u1", log=log)

    assert result.ingested == 0
    assert result.duplicates == 1
    assert result.rejected == []
    assert len(log.attempts()) == 1


def test_duplicate_within_one_batch(tmp_path):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([record("e1"), record("e1")], user_id="u1", log=log)

    assert result.ingested == 1
    assert result.duplicates == 1
    assert len(log.attempts()) == 1


def test_idempotency_is_scoped_to_the_user(tmp_path):
    """Two users pushing the same client-side id are two distinct attempts."""
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1")], user_id="u1", log=log)
    result = ingest_attempts([record("e1")], user_id="u2", log=log)

    assert result.ingested == 1
    assert result.duplicates == 0
    assert len(log.attempts()) == 2


def test_external_id_is_required_on_this_path(tmp_path):
    log = AttemptLog(tmp_path)
    payload = record()
    del payload["external_id"]

    result = ingest_attempts([payload], user_id="u1", log=log)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert log.attempts() == []


def test_malformed_record_does_not_stop_the_batch(tmp_path):
    log = AttemptLog(tmp_path)
    result = ingest_attempts(
        [record("e1"), {"external_id": "e2"}, record("e3")], user_id="u1", log=log
    )

    assert result.ingested == 2
    assert [r.index for r in result.rejected] == [1]
    assert [a.external_id for a in log.attempts()] == ["e1", "e3"]


def test_rejection_carries_a_reason(tmp_path):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([{"external_id": "e1"}], user_id="u1", log=log)

    assert result.rejected[0].reason


def test_empty_batch(tmp_path):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([], user_id="u1", log=log)

    assert result.ingested == 0
    assert result.duplicates == 0
    assert result.rejected == []


def test_push_command_reads_jsonl(tmp_path, monkeypatch, capsys):
    from algo_coach import cli

    source = tmp_path / "attempts.jsonl"
    source.write_text(
        json.dumps(record("e1")) + "\n\n" + json.dumps(record("e2")) + "\n"
    )
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(
        "sys.argv", ["algo-coach", "push", "attempts", str(source), "--user", "u1"]
    )

    cli.main()

    assert AttemptLog(tmp_path / "data").attempts()[0].user_id == "u1"
    assert json.loads(capsys.readouterr().out)["ingested"] == 2


def test_push_command_exits_nonzero_on_rejection(tmp_path, monkeypatch):
    from algo_coach import cli

    source = tmp_path / "attempts.jsonl"
    source.write_text(json.dumps({"external_id": "e1"}) + "\n")
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "push", "attempts", str(source)])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 1
