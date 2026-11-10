import pytest
from helpers import T0
from pydantic import ValidationError
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from algo_coach.knowledge.table import answers, modules, questions, stints, subtopics, topics
from algo_coach.log.table import users
from algo_coach.schema import Answer, Focus, OpenGrade, Stint, StintMode

USER = "u-4f9c2a"
BASE = {
    "id": "r1",
    "client_id": "c1",
    "user_id": USER,
    "device": "phone",
    "at": T0,
    "created_at": T0,
}


def test_ticks_belong_to_an_open_question_s_grade():
    """A choice reply has no points to miss, so a tick without a grade is a
    record of a format it was not."""
    with pytest.raises(ValidationError, match="ticks"):
        Answer(**BASE, question_id="q1", correct=True, missed=[0])


def test_an_open_question_takes_no_guess():
    """A guess is a reply ending in `?`, and an open question takes no reply."""
    with pytest.raises(ValidationError, match="guess"):
        Answer(**BASE, question_id="q1", correct=False, grade=OpenGrade.NONE, guess=True)


def test_an_open_answer_carries_its_ticks():
    answer = Answer(
        **BASE, question_id="q1", correct=False, grade=OpenGrade.PARTIAL, missed=[1], traps=[0]
    )

    assert (answer.missed, answer.traps) == ([1], [0])


@pytest.mark.parametrize(("mode", "level"), [(StintMode.EXAM, None), (StintMode.NEXT, 1)])
def test_an_exam_and_only_an_exam_names_its_level(mode, level):
    """A level exam samples one level, and a queue serves every level."""
    with pytest.raises(ValidationError, match="level"):
        Stint(**BASE, mode=mode, level=level, score=2, answered=4)


@pytest.mark.parametrize(
    "narrowed",
    [
        {"topic_id": "t1"},
        {"module_id": "m1", "subtopic_id": "s1"},
        {"certification_level": 1},
        {"module_id": "m1", "topic_id": "t1", "subtopic_id": "s1", "certification_level": 1},
    ],
)
def test_a_focus_narrows_only_within_what_it_names(narrowed):
    """A subtopic's focus without its topic could not degrade by the content's
    rule, which keeps the level above when the level below is unknown."""
    with pytest.raises(ValidationError):
        Focus(**BASE, **narrowed)


def test_a_focus_naming_nothing_clears_it():
    assert Focus(**BASE).module_id is None


def _one_question(conn) -> None:
    conn.execute(insert(users).values(id=USER, created_at=T0))
    conn.execute(
        insert(modules).values(
            id="m1", slug="python", title="Python", position=0, pass_ratio=0.8,
            kinds=["concept"], code_kinds=[],
        )
    )  # fmt: skip
    conn.execute(
        insert(topics).values(
            id="t1", module_id="m1", slug="core", title="Core", tier=1, position=0
        )
    )
    conn.execute(insert(subtopics).values(id="s1", topic_id="t1", slug="types", position=0))
    conn.execute(
        insert(questions).values(
            id="q1", module_id="m1", subtopic_id="s1", slug="types-1", position=0, level=1,
            kind="concept", format="choice", prompt="?", body={},
        )
    )  # fmt: skip


ANSWER = {**BASE, "question_id": "q1", "correct": True, "guess": False, "missed": [], "traps": []}


def test_a_retried_upload_writes_nothing_twice(database):
    """The client mints `client_id`, and the second copy of one record is
    refused by the table rather than stored beside the first."""
    with database.begin() as conn:
        _one_question(conn)
        conn.execute(insert(answers).values(**ANSWER, wrong=False))
    with pytest.raises(IntegrityError, match="client_id"), database.begin() as conn:
        conn.execute(insert(answers).values(**{**ANSWER, "id": "r2"}, wrong=False))


def test_the_table_refuses_ticks_without_a_grade(database):
    """The record's own rule, held by the database for a writer that skips the
    record."""
    with database.begin() as conn:
        _one_question(conn)
    with pytest.raises(IntegrityError, match="ticks_belong_to_a_grade"), database.begin() as conn:
        conn.execute(insert(answers).values(**ANSWER, wrong=True))


def test_the_table_refuses_an_exam_without_its_rank(database):
    with database.begin() as conn:
        conn.execute(insert(users).values(id=USER, created_at=T0))
    with pytest.raises(IntegrityError, match="an_exam_names_its_level"), database.begin() as conn:
        conn.execute(insert(stints).values(**BASE, mode="exam", score=3, answered=3))
