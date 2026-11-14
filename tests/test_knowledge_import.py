import json
from pathlib import Path

from commands import connected, run_cli
from helpers import T0
from sqlalchemy import insert, select
from test_seed_knowledge import authored

from climb.knowledge import read_module, seed_module
from climb.knowledge.learn import imported, learn_lines
from climb.knowledge.table import answers, stints
from climb.log.table import users

USER = "u-4f9c2a"
T = "2026-11-07T10:00:00+00:00"


def learn_data(tmp_path: Path) -> Path:
    """learn's data repo: a folder per device, a file per month and kind."""
    base = tmp_path / "learn-data"
    phone = base / "progress" / "phone"
    (phone / "sessions").mkdir(parents=True)
    (phone / "status").mkdir()
    lines = [
        {"t": T, "course": "python", "id": "types-1", "ok": True},
        {"t": T, "course": "python", "id": "types-2", "ok": False, "grade": "p", "missed": [1]},
    ]
    (phone / "2026-11.jsonl").write_text("".join(json.dumps(one) + "\n" for one in lines))
    session = {"t": T, "mode": "drill", "score": 1, "n": 2}
    (phone / "sessions" / "2026-11.jsonl").write_text(json.dumps(session) + "\n")
    dropped = {"t": T, "course": "system-design", "status": "archived"}
    (phone / "status" / "2026-11.jsonl").write_text(json.dumps(dropped) + "\n")
    return base


def ready(database, tmp_path) -> Path:
    seed_module(read_module(authored(tmp_path)), root=database)
    with database.begin() as conn:
        conn.execute(insert(users).values(id=USER, created_at=T0))
    return learn_data(tmp_path)


def test_each_line_names_its_kind_and_a_client_id_of_its_place(tmp_path):
    """Derived from the file and the line, so a second import is recognised
    rather than stored again."""
    devices = learn_lines(learn_data(tmp_path))

    first = devices["phone"][0]
    assert first["kind"] == "attempt"
    assert first["client_id"] == "learn:phone/2026-11.jsonl:0"
    assert {one["kind"] for one in devices["phone"]} == {"attempt", "session", "status"}


def test_the_import_stores_what_maps_and_reports_the_rest(database, tmp_path):
    report = imported(database, USER, ready(database, tmp_path))

    assert (report.read, report.stored, report.known) == (4, 3, 0)
    assert [one.reason for one in report.refused] == ["unknown module system-design"]
    with database.connect() as conn:
        assert len(conn.execute(select(answers)).all()) == 2
        assert conn.execute(select(stints.c.mode)).scalar_one() == "filtered"


def test_a_second_import_stores_nothing(database, tmp_path):
    base = ready(database, tmp_path)
    imported(database, USER, base)

    again = imported(database, USER, base)

    assert (again.stored, again.known) == (0, 3)


def test_an_answer_keeps_the_moment_it_was_given(database, tmp_path):
    """The schedule replays answers at the moment the user acted, never at the
    import's."""
    imported(database, USER, ready(database, tmp_path))

    with database.connect() as conn:
        moments = conn.execute(select(answers.c.at)).scalars().all()
    assert {one.isoformat() for one in moments} == {T}


def test_the_terminal_imports_and_prints_the_counts(database, tmp_path, monkeypatch, capsys):
    base = ready(database, tmp_path)
    connected(database, monkeypatch)

    run_cli(monkeypatch, "knowledge", "import", str(base), "--user", USER)

    assert json.loads(capsys.readouterr().out)["stored"] == 3
