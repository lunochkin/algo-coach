from fastapi.testclient import TestClient
from helpers import browsing
from test_seed_knowledge import authored

from algo_coach.api.app import create_app
from algo_coach.knowledge import read_module, seed_module

USER = "u-4f9c2a"
OTHER = "u-7d31b0"
T = "2026-11-09T10:00:00+00:00"


def attempt(client_id: str, **fields) -> dict:
    return {"kind": "attempt", "client_id": client_id, "t": T, "course": "python", "id": "types-1",
            "ok": True, **fields}  # fmt: skip


def synced(database, tmp_path, records, *, user=USER, since=None) -> dict:
    seed_module(read_module(authored(tmp_path)), root=database)
    body = {"device": "phone", "records": records, "since": since or {}}
    response = browsing(database, user).post("/api/knowledge/sync", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_an_answer_is_stored_and_returned_as_it_was_sent(database, tmp_path):
    result = synced(database, tmp_path, [attempt("c1", guess=True)])

    assert result["stored"] == 1
    (back,) = result["records"]
    assert back == {**attempt("c1", guess=True), "device": "phone"}


def test_a_record_sent_twice_is_stored_once(database, tmp_path):
    """A retried upload writes nothing twice: `knowledge.md`, The records."""
    synced(database, tmp_path, [attempt("c1")])

    again = synced(database, tmp_path / "again", [attempt("c1")])

    assert (again["stored"], again["known"]) == (0, 1)
    assert len(again["records"]) == 1


def test_an_open_answer_carries_its_ticks(database, tmp_path):
    ticked = attempt("c1", id="types-2", ok=False, grade="p", missed=[1], traps=[0])

    (back,) = synced(database, tmp_path, [ticked])["records"]

    assert (back["grade"], back["missed"], back["traps"]) == ("p", [1], [0])


def test_learn_s_drill_and_level_exam_map_to_their_names_here(database, tmp_path):
    """Stored under this project's names, returned under learn's, which the
    app still writes."""
    sessions = [
        {"kind": "session", "client_id": "s1", "t": T, "mode": "drill", "score": 3, "n": 4},
        {"kind": "session", "client_id": "s2", "t": T, "mode": "exam-L2", "score": 30, "n": 40},
    ]

    back = synced(database, tmp_path, sessions)["records"]

    assert [one["mode"] for one in back] == ["drill", "exam-L2"]


def test_a_certification_focus_names_its_topic_and_level(database, tmp_path):
    focus = {"kind": "focus", "client_id": "f1", "t": T, "course": "python", "topic": "core",
             "sub": None, "strict": True, "cert": "python-core-associate"}  # fmt: skip

    (back,) = synced(database, tmp_path, [focus])["records"]

    assert back["cert"] == "python-core-associate"
    assert back["strict"] is True


def test_a_whole_module_certification_names_no_topic(database, tmp_path):
    cert = {"kind": "cert", "client_id": "x1", "t": T, "course": "python",
            "cert": "python-all-expert", "score": 28, "n": 30, "passed": False}  # fmt: skip

    (back,) = synced(database, tmp_path, [cert])["records"]

    assert back["cert"] == "python-all-expert"


def test_statuses_and_lesson_marks_round_trip(database, tmp_path):
    records = [
        {"kind": "status", "client_id": "m1", "t": T, "course": "python", "status": "paused"},
        {"kind": "lesson", "client_id": "l1", "t": T, "course": "python", "lesson": "names",
         "status": "undone"},
    ]  # fmt: skip

    back = synced(database, tmp_path, records)["records"]

    assert {one["kind"]: one.get("status") for one in back} == {
        "status": "paused",
        "lesson": "undone",
    }


def setting(client_id: str, name: str, n: int) -> dict:
    return {"kind": "setting", "client_id": client_id, "t": T, "name": name, "n": n}


def test_the_settings_and_a_raise_round_trip(database, tmp_path):
    """None names content, so every device receives each as sent."""
    records = [
        setting("d1", "new_per_day", 15),
        setting("e1", "exam_size", 30),
        {"kind": "raise", "client_id": "r1", "t": T, "n": 5},
    ]

    back = synced(database, tmp_path, records)["records"]

    assert {one.get("name", one["kind"]): one["n"] for one in back} == {
        "new_per_day": 15,
        "exam_size": 30,
        "raise": 5,
    }


def test_a_setting_out_of_its_range_is_refused(database, tmp_path):
    """An exam samples one question at least, and a day may allow no new one."""
    records = [setting("e1", "exam_size", 0), setting("d1", "new_per_day", 0)]

    result = synced(database, tmp_path, records)

    assert [one["client_id"] for one in result["refused"]] == ["e1"]
    assert result["stored"] == 1


def test_a_setting_the_engine_does_not_know_is_refused(database, tmp_path):
    result = synced(database, tmp_path, [setting("x1", "volume", 3)])

    assert [one["client_id"] for one in result["refused"]] == ["x1"]


def test_a_raise_adds_at_least_one_question(database, tmp_path):
    result = synced(database, tmp_path, [{"kind": "raise", "client_id": "r1", "t": T, "n": 0}])

    assert [one["client_id"] for one in result["refused"]] == ["r1"]


def test_the_module_order_round_trips_by_slug(database, tmp_path):
    """Stored as minted ids, returned as the slugs the client sent."""
    order = {"kind": "order", "client_id": "o1", "t": T, "courses": ["python"]}

    (back,) = synced(database, tmp_path, [order])["records"]

    assert back["courses"] == ["python"]


def test_an_order_naming_an_unknown_module_is_refused(database, tmp_path):
    order = {"kind": "order", "client_id": "o1", "t": T, "courses": ["python", "nowhere"]}

    result = synced(database, tmp_path, [order])

    assert result["refused"] == [{"client_id": "o1", "reason": "unknown module nowhere"}]


def test_an_order_that_is_no_list_of_slugs_is_refused(database, tmp_path):
    order = {"kind": "order", "client_id": "o1", "t": T, "courses": "python"}

    (refused,) = synced(database, tmp_path, [order])["refused"]

    assert refused["reason"] == "courses: a list of module slugs"


def test_a_record_naming_unknown_content_is_refused_alone(database, tmp_path):
    """One bad record leaves the rest of the upload stored, and the client
    learns which one to drop."""
    result = synced(database, tmp_path, [attempt("c1", id="nowhere-9"), attempt("c2")])

    assert result["stored"] == 1
    assert result["refused"] == [{"client_id": "c1", "reason": "unknown question python/nowhere-9"}]


def test_the_cursor_returns_only_what_came_after_it(database, tmp_path):
    first = synced(database, tmp_path, [attempt("c1")])

    later = synced(database, tmp_path / "again", [attempt("c2")], since=first["cursor"])

    assert [one["client_id"] for one in later["records"]] == ["c2"]


def test_the_reply_names_whose_log_it_is(database, tmp_path):
    assert synced(database, tmp_path, [])["user_id"] == USER


def test_a_user_never_receives_another_user_s_records(database, tmp_path):
    synced(database, tmp_path, [attempt("c1")], user=OTHER)

    mine = synced(database, tmp_path / "again", [], user=USER)

    assert mine["records"] == []


def test_the_sync_needs_a_signed_in_user(database):
    client = TestClient(create_app(database), headers={"content-type": "application/json"})

    assert (
        client.post("/api/knowledge/sync", json={"device": "phone", "records": []}).status_code
        == 401
    )
