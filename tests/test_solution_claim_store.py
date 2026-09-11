from helpers import PROVENANCE

from algo_coach.mint import machine_solution_claim, user_solution_claim
from algo_coach.solution_claims import SolutionClaimLog


def make_solution_claim(solution_id: str = "s1", techniques: list[str] | None = None):
    return machine_solution_claim(
        solution_id, techniques or ["two-pointers"], provenance=PROVENANCE
    )


def test_an_empty_store_reads_as_nothing(database):
    assert SolutionClaimLog(database).claims() == []
    assert SolutionClaimLog(database).for_solution("s1") == []


def test_a_reading_reads_back_whole(database):
    log = SolutionClaimLog(database)
    claim = make_solution_claim()
    log.append(claim)

    assert log.claims() == [claim]


def test_an_empty_verdict_is_stored(database):
    """A claim naming nothing is the verdict that no code in the vocabulary
    describes this solution, and unstored it would be paid for again."""
    log = SolutionClaimLog(database)
    declined = make_solution_claim(techniques=[])
    log.append(declined)

    assert log.claims() == [declined]


def test_a_later_reading_appends_rather_than_replacing(database):
    """Append-only: a re-run at a new configuration lands beside the earlier
    verdict, which stays readable."""
    log = SolutionClaimLog(database)
    first = make_solution_claim(techniques=["two-pointers"])
    again = make_solution_claim(techniques=["two-pointers", "sorting"])
    log.append(first)
    log.append(again)

    assert log.claims() == [first, again]


def test_a_hand_reading_lands_beside_a_machine_one(database):
    """One store for both writers. Which of them stands is the record's
    question, not the log's."""
    log = SolutionClaimLog(database)
    machine = make_solution_claim()
    user = user_solution_claim("s1", ["sorting"])
    log.append(machine)
    log.append(user)

    assert log.claims() == [machine, user]


def test_the_set_is_read_per_solution(database):
    """A problem's techniques are folded from the claims of its canonicals,
    and a solution is what a claim is keyed to."""
    log = SolutionClaimLog(database)
    mine = [make_solution_claim("s1"), make_solution_claim("s1", ["sorting"])]
    theirs = make_solution_claim("s2")
    for one in [*mine, theirs]:
        log.append(one)

    assert log.for_solution("s1") == mine
    assert log.for_solution("s2") == [theirs]


def test_append_order_is_kept(database):
    """A tie on `created_at` is broken by what landed last, which only holds
    if the file is read in the order it was written."""
    log = SolutionClaimLog(database)
    written = [make_solution_claim(f"s{n}") for n in range(5)]
    for one in written:
        log.append(one)

    assert [one.id for one in log.claims()] == [one.id for one in written]
