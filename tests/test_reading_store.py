"""The reading log: append-only, as the match log is and for the same reason —
a re-run appends its verdict where an earlier one stays readable.
"""

from helpers import PROVENANCE

from algo_coach.mint import machine_reading, user_reading
from algo_coach.readings import ReadingLog


def make_reading(solution_id: str = "s1", techniques: list[str] | None = None):
    return machine_reading(solution_id, techniques or ["two-pointers"], **PROVENANCE)


def test_an_empty_store_reads_as_nothing(tmp_path):
    assert ReadingLog(tmp_path).readings() == []
    assert ReadingLog(tmp_path).for_solution("s1") == []


def test_a_reading_reads_back_whole(tmp_path):
    log = ReadingLog(tmp_path)
    reading = make_reading()
    log.append(reading)

    assert log.readings() == [reading]


def test_an_empty_verdict_is_stored(tmp_path):
    """A reading naming nothing is the verdict that no code in the vocabulary
    describes this solution, and unstored it would be paid for again."""
    log = ReadingLog(tmp_path)
    declined = make_reading(techniques=[])
    log.append(declined)

    assert log.readings() == [declined]


def test_a_later_reading_appends_rather_than_replacing(tmp_path):
    """Append-only: a re-run at a new configuration lands beside the earlier
    verdict, which stays readable."""
    log = ReadingLog(tmp_path)
    first = make_reading(techniques=["two-pointers"])
    again = make_reading(techniques=["two-pointers", "sorting"])
    log.append(first)
    log.append(again)

    assert log.readings() == [first, again]


def test_a_hand_reading_lands_beside_a_machine_one(tmp_path):
    """One store for both writers. Which of them stands is the record's
    question, not the log's."""
    log = ReadingLog(tmp_path)
    machine = make_reading()
    hand = user_reading("s1", ["sorting"])
    log.append(machine)
    log.append(hand)

    assert log.readings() == [machine, hand]


def test_the_set_is_read_per_solution(tmp_path):
    """A problem's techniques are folded from the readings of its canonicals,
    and a solution is what a reading is keyed to."""
    log = ReadingLog(tmp_path)
    mine = [make_reading("s1"), make_reading("s1", ["sorting"])]
    theirs = make_reading("s2")
    for one in [*mine, theirs]:
        log.append(one)

    assert log.for_solution("s1") == mine
    assert log.for_solution("s2") == [theirs]


def test_append_order_is_kept(tmp_path):
    """A tie on `created_at` is broken by what landed last, which only holds
    if the file is read in the order it was written."""
    log = ReadingLog(tmp_path)
    written = [make_reading(f"s{n}") for n in range(5)]
    for one in written:
        log.append(one)

    assert [one.id for one in log.readings()] == [one.id for one in written]
