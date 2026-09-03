from helpers import PROVENANCE

from algo_coach.mint import solution
from algo_coach.schema import SolutionRole
from algo_coach.solutions import SolutionLog


def make_canonical(
    problem_id: str = "p1",
    code: str = "def solve(n):\n    return n\n",
    role: SolutionRole = SolutionRole.CANONICAL,
):
    return solution(problem_id=problem_id, code=code, role=role, **PROVENANCE)


def test_an_empty_store_reads_as_nothing(tmp_path):
    assert SolutionLog(tmp_path).solutions() == []
    assert SolutionLog(tmp_path).for_problem("p1") == []


def test_a_canonical_reads_back_whole(tmp_path):
    """Code carries newlines, so the round trip is what says the store can
    hold a solution rather than a summary of one."""
    store = SolutionLog(tmp_path)
    canonical = make_canonical()
    store.append(canonical)

    assert store.solutions() == [canonical]


def test_a_second_canonical_lands_beside_the_first(tmp_path):
    """Appended, never replacing. A problem carrying one canonical can teach
    one form, and the second is what covers the other."""
    store = SolutionLog(tmp_path)
    sorted_first = make_canonical(code="def solve(xs):\n    return sorted(xs)[0]\n")
    scanned = make_canonical(code="def solve(xs):\n    return min(xs)\n")
    store.append(sorted_first)
    store.append(scanned)

    assert store.solutions() == [sorted_first, scanned]


def test_the_set_is_read_per_problem(tmp_path):
    """What a problem's techniques derive from, and what a matcher reads
    beside its statement."""
    store = SolutionLog(tmp_path)
    mine = [make_canonical("p1"), make_canonical("p1")]
    theirs = make_canonical("p2")
    for one in [*mine, theirs]:
        store.append(one)

    assert store.for_problem("p1") == mine
    assert store.for_problem("p2") == [theirs]


def test_a_problem_with_no_canonical_reads_as_nothing(tmp_path):
    """Nothing lands until a canonical passes, so this is a store that has not
    been written to rather than a problem that shipped without one."""
    store = SolutionLog(tmp_path)
    store.append(make_canonical("p1"))

    assert store.for_problem("p2") == []


def test_append_order_is_kept(tmp_path):
    """A tie on `created_at` is broken by what landed last, which only holds
    if the file is read in the order it was written."""
    store = SolutionLog(tmp_path)
    written = [make_canonical(code=f"def solve():\n    return {n}\n") for n in range(5)]
    for one in written:
        store.append(one)

    assert [one.id for one in store.solutions()] == [one.id for one in written]


def test_the_set_is_read_per_role(tmp_path):
    """A problem's techniques derive from its canonicals alone. The reference
    is the naive approach the form replaces, so counting it would credit the
    problem with a technique nothing about it teaches."""
    store = SolutionLog(tmp_path)
    canonical = make_canonical()
    reference = make_canonical(role=SolutionRole.REFERENCE)
    store.append(canonical)
    store.append(reference)

    assert store.for_problem("p1") == [canonical, reference]
    assert store.for_problem("p1", SolutionRole.CANONICAL) == [canonical]
    assert store.for_problem("p1", SolutionRole.REFERENCE) == [reference]
