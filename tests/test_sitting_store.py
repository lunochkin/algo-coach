from algo_coach.log import SittingStore
from algo_coach.schema import Attempt, Sitting

CONTENT = {
    "user_id": "maks",
    "problem_id": "p1",
    "started_at": "2026-09-10T08:00:00Z",
}
AT_NINE = "2026-09-10T09:00:00Z"
AT_TEN = "2026-09-10T10:00:00Z"


def a_sitting(id: str = "s1", **overrides) -> Sitting:
    return Sitting.model_validate(CONTENT | {"id": id} | overrides)


def test_put_and_get(tmp_path):
    store = SittingStore(tmp_path)
    sitting = a_sitting()
    store.put(sitting)

    assert store.get("s1") == sitting


def test_get_missing_is_none(tmp_path):
    assert SittingStore(tmp_path).get("nope") is None


def test_all_on_empty_store(tmp_path):
    assert SittingStore(tmp_path).all() == []


def test_a_sitting_is_revised_in_place(tmp_path):
    """A pause moves the sitting it was taken in, where every append-only store
    would hold two records and leave the reader to order them."""
    store = SittingStore(tmp_path)
    store.put(a_sitting())
    store.put(a_sitting(pauses=[{"at": AT_NINE}]))

    assert store.get("s1").paused
    assert len(store.all()) == 1


def test_an_ended_sitting_is_kept(tmp_path):
    """How often practice is interrupted is readable in this store alone, so
    ending a sitting removes nothing."""
    store = SittingStore(tmp_path)
    store.put(a_sitting(pauses=[{"at": AT_NINE, "until": AT_TEN}], ended_at=AT_TEN))

    assert store.get("s1").ended_at is not None
    assert len(store.all()) == 1


def test_the_store_clears_nothing(tmp_path):
    """The draft store removes what landed; a sitting has no such exit."""
    assert not hasattr(SittingStore(tmp_path), "remove")


def test_the_pauses_read_back_whole(tmp_path):
    """The intervals are the record's own evidence, so a round trip that
    flattened them to a total would lose how often the sitting stopped."""
    store = SittingStore(tmp_path)
    store.put(a_sitting(pauses=[{"at": AT_NINE, "until": AT_TEN}, {"at": AT_TEN}]))

    assert [one.until is None for one in store.get("s1").pauses] == [False, True]


def test_sittings_are_read_in_id_order(tmp_path):
    store = SittingStore(tmp_path)
    for id in ("s2", "s1"):
        store.put(a_sitting(id))

    assert [one.id for one in store.all()] == ["s1", "s2"]


def test_an_attempt_names_the_sitting_it_was_made_in(tmp_path):
    """The log is append-only, so an attempt written without the id can never
    be grouped with the sitting's others."""
    attempt = Attempt.model_validate(
        {
            "id": "a1",
            "user_id": "maks",
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
        {"id": "a1", "user_id": "maks", "problem_id": "p1", "finished_at": AT_TEN, "solved": False}
    )
    assert attempt.sitting_id is None


def test_a_running_sitting_is_found_by_user_and_problem(tmp_path):
    store = SittingStore(tmp_path)
    store.put(a_sitting())

    assert store.running("maks", "p1").id == "s1"


def test_an_ended_sitting_is_not_running(tmp_path):
    store = SittingStore(tmp_path)
    store.put(a_sitting(ended_at=AT_TEN))

    assert store.running("maks", "p1") is None


def test_another_user_s_sitting_is_not_running(tmp_path):
    store = SittingStore(tmp_path)
    store.put(a_sitting(user_id="someone"))

    assert store.running("maks", "p1") is None
