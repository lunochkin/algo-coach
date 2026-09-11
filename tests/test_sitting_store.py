import pytest
from helpers import stored_problem

from algo_coach.log import SittingStore
from algo_coach.schema import Attempt, Sitting


@pytest.fixture(autouse=True)
def referenced(database):
    """The problem this module's sittings and attempts name."""
    stored_problem(database, "p1")


CONTENT = {
    "user_id": "u-4f9c2a",
    "problem_id": "p1",
    "started_at": "2026-09-10T08:00:00Z",
}
AT_NINE = "2026-09-10T09:00:00Z"
AT_TEN = "2026-09-10T10:00:00Z"


def a_sitting(id: str = "s1", **overrides) -> Sitting:
    return Sitting.model_validate(CONTENT | {"id": id} | overrides)


def test_put_and_get(database):
    store = SittingStore(database)
    sitting = a_sitting()
    store.put(sitting)

    assert store.get("s1") == sitting


def test_get_missing_is_none(database):
    assert SittingStore(database).get("nope") is None


def test_all_on_empty_store(database):
    assert SittingStore(database).all() == []


def test_a_sitting_is_revised_in_place(database):
    """A pause moves the sitting it was taken in, where every append-only store
    would hold two records and leave the reader to order them."""
    store = SittingStore(database)
    store.put(a_sitting())
    store.put(a_sitting(pauses=[{"at": AT_NINE}]))

    assert store.get("s1").paused
    assert len(store.all()) == 1


def test_an_ended_sitting_is_kept(database):
    """How often practice is interrupted is readable in this store alone, so
    ending a sitting removes nothing."""
    store = SittingStore(database)
    store.put(a_sitting(pauses=[{"at": AT_NINE, "until": AT_TEN}], ended_at=AT_TEN))

    assert store.get("s1").ended_at is not None
    assert len(store.all()) == 1


def test_the_store_clears_nothing(database):
    """The draft store removes what landed; a sitting has no such exit."""
    assert not hasattr(SittingStore(database), "remove")


def test_the_pauses_read_back_whole(database):
    """The intervals are the record's own evidence, so a round trip that
    flattened them to a total would lose how often the sitting stopped."""
    store = SittingStore(database)
    store.put(a_sitting(pauses=[{"at": AT_NINE, "until": AT_TEN}, {"at": AT_TEN}]))

    assert [one.until is None for one in store.get("s1").pauses] == [False, True]


def test_sittings_are_read_in_id_order(database):
    store = SittingStore(database)
    for id in ("s2", "s1"):
        # ended, since one clock runs on a problem for a user at a time
        store.put(a_sitting(id, ended_at=AT_TEN))

    assert [one.id for one in store.all()] == ["s1", "s2"]


def test_an_attempt_names_the_sitting_it_was_made_in(tmp_path):
    """The log is append-only, so an attempt written without the id can never
    be grouped with the sitting's others."""
    attempt = Attempt.model_validate(
        {
            "id": "a1",
            "user_id": "u-4f9c2a",
            "problem_id": "p1",
            "sitting_id": "s1",
            "finished_at": AT_TEN,
            "solved": True,
        }
    )
    assert attempt.sitting_id == "s1"


def test_an_attempt_no_sitting_minted_carries_none():
    """Every attempt of the pushed corpus predates the engine serving one."""
    attempt = Attempt.model_validate(
        {
            "id": "a1",
            "user_id": "u-4f9c2a",
            "problem_id": "p1",
            "finished_at": AT_TEN,
            "solved": False,
        }
    )
    assert attempt.sitting_id is None


def test_a_running_sitting_is_found_by_user_and_problem(database):
    store = SittingStore(database)
    store.put(a_sitting())

    assert store.running("u-4f9c2a", "p1").id == "s1"


def test_an_ended_sitting_is_not_running(database):
    store = SittingStore(database)
    store.put(a_sitting(ended_at=AT_TEN))

    assert store.running("u-4f9c2a", "p1") is None


def test_another_user_s_sitting_is_not_running(database):
    store = SittingStore(database)
    store.put(a_sitting(user_id="u-b71e03"))

    assert store.running("u-4f9c2a", "p1") is None
