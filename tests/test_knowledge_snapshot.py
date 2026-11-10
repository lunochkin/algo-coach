from fastapi.testclient import TestClient
from helpers import browsing
from test_seed_knowledge import CHOICE, authored, titled

from algo_coach.api.app import create_app
from algo_coach.knowledge import read_module, seed_module

USER = "u-4f9c2a"


def snapshot(database, tmp_path, **files) -> dict:
    seed_module(read_module(authored(tmp_path, **files)), root=database)
    response = browsing(database, USER).get("/api/knowledge/snapshot")
    assert response.status_code == 200
    return response.json()


def test_the_snapshot_is_the_format_learn_s_app_reads(database, tmp_path):
    """Format 6, so the app's loader stays as it is: `knowledge.md`."""
    served = snapshot(database, tmp_path)

    assert served["format"] == 6
    assert served["rules"]["fsrs"]["enable_fuzzing"] is False
    assert served["rules"]["levels"] == {
        "0": "Foundation",
        "1": "Associate",
        "2": "Professional",
        "3": "Expert",
    }


def test_a_module_reads_as_learn_s_course(database, tmp_path):
    (course,) = snapshot(database, tmp_path)["courses"]

    assert course["slug"] == "python"
    assert course["definition"]["topic"] == [
        {"slug": "core", "tier": 1, "title": "Core", "subs": ["types", "flow"]}
    ]
    assert [(q["id"], q["topic"], q["sub"]) for q in course["questions"]] == [
        ("types-1", "core", "types"),
        ("types-2", "core", "types"),
        ("flow-1", "core", "flow"),
    ]


def test_an_open_question_reaches_the_app_as_learn_s_card(database, tmp_path):
    """The rename stops at the engine's edge, where learn's app still reads
    `card`."""
    (course,) = snapshot(database, tmp_path)["courses"]

    formats = {q["id"]: q.get("format", "choice") for q in course["questions"]}
    assert formats == {"types-1": "choice", "types-2": "card", "flow-1": "short"}


def test_a_question_reads_back_as_it_was_authored(database, tmp_path):
    (course,) = snapshot(database, tmp_path)["courses"]

    first = course["questions"][0]
    assert first["level"] == 0
    assert first["answer"] == ["B"]
    assert first["lesson"] == "names#binding"
    assert "code" not in first


def test_lessons_reach_the_app_with_their_bodies(database, tmp_path):
    (course,) = snapshot(database, tmp_path)["courses"]

    assert course["graph"]["format"] == 2
    assert course["graph"]["lesson"]["names"]["teaches"] == ["types@0"]
    assert course["lesson_bodies"]["names"].startswith("# Names")


def test_a_retired_question_is_not_served(database, tmp_path):
    seed_module(read_module(authored(tmp_path)), root=database)

    (course,) = snapshot(database, tmp_path / "again", types=CHOICE)["courses"]

    assert [q["id"] for q in course["questions"]] == ["types-1", "flow-1"]


def test_the_snapshot_needs_a_signed_in_user(database):
    assert TestClient(create_app(database)).get("/api/knowledge/snapshot").status_code == 401


def test_an_unchanged_snapshot_answers_304(database, tmp_path):
    """The app syncs often, and the content moves only at a seed."""
    seed_module(read_module(authored(tmp_path)), root=database)
    client = browser_of(database)
    first = client.get("/api/knowledge/snapshot")

    again = client.get("/api/knowledge/snapshot", headers={"if-none-match": first.headers["etag"]})

    assert again.status_code == 304


def test_a_seed_changes_the_snapshot_s_tag(database, tmp_path):
    seed_module(read_module(authored(tmp_path)), root=database)
    client = browser_of(database)
    first = client.get("/api/knowledge/snapshot").headers["etag"]

    seed_module(read_module(authored(tmp_path / "again", types=CHOICE)), root=database)

    assert client.get("/api/knowledge/snapshot").headers["etag"] != first


def browser_of(database):
    return browsing(database, USER)


def test_a_titled_subtopic_reaches_the_app_by_its_title(database, tmp_path):
    seed_module(read_module(titled(tmp_path)), root=database)

    (course,) = browser_of(database).get("/api/knowledge/snapshot").json()["courses"]
    assert course["definition"]["topic"][0]["sub_titles"] == {"types": "Mutability and identity"}


def test_a_topic_with_no_titles_reads_as_learn_wrote_it(database, tmp_path):
    """The key is left out, so a module without titles still equals learn's."""
    (course,) = snapshot(database, tmp_path)["courses"]

    assert "sub_titles" not in course["definition"]["topic"][0]
