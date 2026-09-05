from helpers import WRITTEN

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.schema import TestCase


def case(*args, **overrides) -> TestCase:
    return mint.case(*args, written=WRITTEN, **overrides)


def test_an_empty_store_reads_as_nothing(tmp_path):
    assert CaseLog(tmp_path).cases() == []
    assert CaseLog(tmp_path).for_problem("p1") == []


def test_a_case_reads_back_whole(tmp_path):
    """Arguments and returns are whatever the problem asks for, so the round
    trip is what says the store holds them rather than a summary."""
    store = CaseLog(tmp_path)
    one = case("p1", [[2, 7], {"k": 1}, "s", 1.5, True, None], [0, 1])
    store.append(one)

    assert store.cases() == [one]


def test_an_added_case_lands_beside_the_set(tmp_path):
    """An edge case, or one sized to force a timeout, is appended rather than
    replacing what was written with the statement."""
    store = CaseLog(tmp_path)
    written = case("p1", [[2, 7, 11, 15], 9], [0, 1])
    edge = case("p1", [[], 0], [])
    store.append(written)
    store.append(edge)

    assert store.cases() == [written, edge]


def test_the_set_is_read_per_problem(tmp_path):
    """Every problem carries the cases that decide it, and a run covers that
    set whole."""
    store = CaseLog(tmp_path)
    mine = [case("p1", [1], 1), case("p1", [2], 4)]
    theirs = case("p2", [3], 9)
    for one in [*mine, theirs]:
        store.append(one)

    assert store.for_problem("p1") == mine
    assert store.for_problem("p2") == [theirs]


def test_append_order_is_the_order_a_run_decides_them_in(tmp_path):
    store = CaseLog(tmp_path)
    written = [case("p1", [n], n * n) for n in range(5)]
    for one in written:
        store.append(one)

    assert [one.id for one in store.cases()] == [one.id for one in written]
