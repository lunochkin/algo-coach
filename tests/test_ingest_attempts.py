import json
from datetime import UTC, datetime

import pytest

from algo_coach import cli
from algo_coach.ingest import ingest_attempts
from algo_coach.log import AttemptLog
from algo_coach.schema import VerdictSource


def record(external_id: str = "e1", **overrides) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "external_id": external_id,
        "problem_external_id": "p1",
        "started_at": now,
        "finished_at": now,
        "code": "def f(): pass",
        "solved": True,
        "time_to_solve_sec": 900.0,
    } | overrides


def test_valid_record_is_appended(tmp_path, problems):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([record()], user_id="u1", log=log, problems=problems)

    assert result.ingested == 1
    assert result.duplicates == 0
    assert result.rejected == []
    assert [a.external_id for a in log.attempts()] == ["e1"]


def test_identity_comes_from_the_adapter(tmp_path, problems):
    log = AttemptLog(tmp_path)
    ingest_attempts([record()], user_id="u1", log=log, problems=problems)

    assert log.attempts()[0].user_id == "u1"


def test_payload_cannot_supply_identity(tmp_path, problems):
    """A client sending its own id, user_id or problem_id has them dropped."""
    log = AttemptLog(tmp_path)
    ingest_attempts(
        [record(id="forged", user_id="someone-else", problem_id="forged")],
        user_id="u1",
        log=log,
        problems=problems,
    )

    attempt = log.attempts()[0]
    assert attempt.user_id == "u1"
    assert attempt.id != "forged"
    assert attempt.problem_id == "minted-u1"


def test_verdict_is_marked_as_the_client_s(tmp_path, problems):
    """Nothing on this path ran the tests, whatever the payload asserts."""
    log = AttemptLog(tmp_path)
    ingest_attempts(
        [record(verdict_source="engine")], user_id="u1", log=log, problems=problems
    )

    assert log.attempts()[0].verdict_source is VerdictSource.CLIENT


def test_engine_mints_distinct_ids(tmp_path, problems):
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1"), record("e2")], user_id="u1", log=log, problems=problems)

    ids = [a.id for a in log.attempts()]
    assert len(set(ids)) == 2


def test_re_push_is_a_no_op(tmp_path, problems):
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1")], user_id="u1", log=log, problems=problems)
    result = ingest_attempts([record("e1")], user_id="u1", log=log, problems=problems)

    assert result.ingested == 0
    assert result.duplicates == 1
    assert result.rejected == []
    assert len(log.attempts()) == 1


def test_duplicate_within_one_batch(tmp_path, problems):
    log = AttemptLog(tmp_path)
    result = ingest_attempts(
        [record("e1"), record("e1")], user_id="u1", log=log, problems=problems
    )

    assert result.ingested == 1
    assert result.duplicates == 1
    assert len(log.attempts()) == 1


def test_idempotency_is_scoped_to_the_user(tmp_path, problems):
    """Two users pushing the same client-side id are two distinct attempts."""
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1")], user_id="u1", log=log, problems=problems)
    result = ingest_attempts([record("e1")], user_id="u2", log=log, problems=problems)

    assert result.ingested == 1
    assert result.duplicates == 0
    assert len(log.attempts()) == 2


def test_external_id_is_required_on_this_path(tmp_path, problems):
    log = AttemptLog(tmp_path)
    payload = record()
    del payload["external_id"]

    result = ingest_attempts([payload], user_id="u1", log=log, problems=problems)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert log.attempts() == []


def test_malformed_record_does_not_stop_the_batch(tmp_path, problems):
    log = AttemptLog(tmp_path)
    result = ingest_attempts(
        [record("e1"), {"external_id": "e2"}, record("e3")],
        user_id="u1",
        log=log,
        problems=problems,
    )

    assert result.ingested == 2
    assert [r.index for r in result.rejected] == [1]
    assert [a.external_id for a in log.attempts()] == ["e1", "e3"]


def test_rejection_carries_a_reason(tmp_path, problems):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([{"external_id": "e1"}], user_id="u1", log=log, problems=problems)

    assert result.rejected[0].reason


def test_empty_batch(tmp_path, problems):
    log = AttemptLog(tmp_path)
    result = ingest_attempts([], user_id="u1", log=log, problems=problems)

    assert result.ingested == 0
    assert result.duplicates == 0
    assert result.rejected == []


def test_push_command_reads_jsonl(tmp_path, monkeypatch, capsys, data_root):
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


def test_push_command_reports_a_line_that_is_not_json(
    tmp_path, monkeypatch, capsys, data_root
):
    """Corrupt transport, not an invalid record: ingest never sees the line,
    so it exits with the line number instead of a traceback."""
    source = tmp_path / "attempts.jsonl"
    source.write_text(json.dumps(record("e1")) + "\nnot json\n")
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "push", "attempts", str(source)])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2
    assert "line 2" in capsys.readouterr().err
    assert len(AttemptLog(tmp_path / "data").attempts()) == 1


def test_push_command_exits_nonzero_on_rejection(tmp_path, monkeypatch, data_root):
    source = tmp_path / "attempts.jsonl"
    source.write_text(json.dumps({"external_id": "e1"}) + "\n")
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr("sys.argv", ["algo-coach", "push", "attempts", str(source)])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 1


def test_unknown_problem_is_rejected(tmp_path, problems):
    """The log must not hold a reference nothing can follow."""
    log = AttemptLog(tmp_path)
    result = ingest_attempts(
        [record(problem_external_id="never-pushed")], user_id="u1", log=log, problems=problems
    )

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]
    assert log.attempts() == []


def test_problem_reference_is_required(tmp_path, problems):
    log = AttemptLog(tmp_path)
    payload = record()
    del payload["problem_external_id"]

    result = ingest_attempts([payload], user_id="u1", log=log, problems=problems)

    assert result.ingested == 0
    assert [r.index for r in result.rejected] == [0]


def test_problem_resolution_is_scoped_to_the_user(tmp_path, problems):
    """The same platform slug resolves to each user's own problem."""
    log = AttemptLog(tmp_path)
    ingest_attempts([record("e1")], user_id="u1", log=log, problems=problems)
    ingest_attempts([record("e1")], user_id="u2", log=log, problems=problems)

    assert [a.problem_id for a in log.attempts()] == ["minted-u1", "minted-u2"]


def test_external_reference_is_not_stored_on_the_record(tmp_path, problems):
    """problem_external_id is transport: the record holds the minted id only."""
    log = AttemptLog(tmp_path)
    ingest_attempts([record()], user_id="u1", log=log, problems=problems)

    assert "problem_external_id" not in log.attempts()[0].model_dump()
