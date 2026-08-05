"""The order a hand-claim sample is drawn in.

The pool is skewed the way a backlog is: many problems on one pair of tags,
a few on the rest. What these check is that a prefix of the order is spread
across techniques rather than drawn from whatever dominates.
"""

from helpers import attempt, seed_problem

from algo_coach.claims import spread
from algo_coach.problems import ProblemStore


def techniques_of(problems, drawn):
    return {code for one in drawn for code in problems[one.problem_id].techniques}


def pool(root, tagged: dict[str, list[str]]):
    """One problem per entry, an attempt on each. Returns the attempts and the
    stored problems, which is what `spread` reads the techniques from."""
    for id, tags in tagged.items():
        seed_problem(root, id=id, tags=tags)
    attempts = [attempt(f"a-{id}", id) for id in tagged]
    return attempts, {problem.id: problem for problem in ProblemStore(root).all()}


def skewed(root, *, common: int):
    """`common` problems on the same two tags, and one problem each on three
    other pairs — the shape a real backlog has."""
    tagged = {f"common{n}": ["Greedy", "Sorting"] for n in range(common)}
    tagged["rare1"] = ["Trie", "Dynamic Programming"]
    tagged["rare2"] = ["Backtracking", "Binary Search"]
    tagged["rare3"] = ["Two Pointers", "Sliding Window"]
    return pool(root, tagged)


def test_a_short_prefix_covers_every_technique(tmp_path):
    """A uniform shuffle would put a sample this size almost all on the pair
    the backlog holds most of, and the score is read per technique."""
    attempts, problems = skewed(tmp_path, common=40)

    drawn = spread(attempts, problems)[:4]

    assert len(techniques_of(problems, drawn)) == 8


def test_the_dominant_technique_takes_one_turn_like_the_rest(tmp_path):
    attempts, problems = skewed(tmp_path, common=40)

    drawn = spread(attempts, problems)[:4]

    assert [one.problem_id.startswith("common") for one in drawn].count(True) == 1


def test_a_technique_already_covered_waits(tmp_path):
    """Covering one technique often covers another, since a claim decides
    every tag its problem carries."""
    attempts, problems = pool(
        tmp_path,
        {
            "both": ["Greedy", "Sorting"],
            "greedy-again": ["Greedy", "Sorting"],
            "elsewhere": ["Trie", "Backtracking"],
        },
    )

    first, second, _ = spread(attempts, problems)

    assert techniques_of(problems, [first]).isdisjoint(techniques_of(problems, [second]))


def test_every_attempt_is_drawn_once(tmp_path):
    attempts, problems = skewed(tmp_path, common=10)

    drawn = spread(attempts, problems)

    assert sorted(one.id for one in drawn) == sorted(one.id for one in attempts)


def test_the_same_seed_gives_the_same_order(tmp_path):
    attempts, problems = skewed(tmp_path, common=10)

    assert [one.id for one in spread(attempts, problems, seed=7)] == [
        one.id for one in spread(attempts, problems, seed=7)
    ]


def test_another_seed_gives_another_order(tmp_path):
    """Within a technique the choice is the seed's; a sample is described by
    it rather than by listing what it held."""
    attempts, problems = skewed(tmp_path, common=10)

    assert [one.id for one in spread(attempts, problems, seed=0)] != [
        one.id for one in spread(attempts, problems, seed=1)
    ]


def test_an_empty_pool_is_an_empty_order(tmp_path):
    assert spread([], {}) == []
