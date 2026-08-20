"""The order a hand-claim sample is drawn in.

The pool is skewed the way a backlog is: many problems on one pair of tags,
a few on the rest. What these check is that a prefix of the order is spread
across techniques rather than drawn from whatever dominates.
"""

from collections import Counter

from helpers import attempt, seed_problem

from algo_coach.claims import claimable, spread
from algo_coach.mint import user_claim
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


def test_a_technique_already_claimed_waits_like_a_covered_one(tmp_path):
    """The eval set is grown, not drawn fresh. What `spread` levels is the
    claimed set plus the sample, so a technique the hand pass already reached
    forty times is behind one it has never reached — the same rule as within a
    batch, extended to what was claimed before it."""
    attempts, problems = pool(
        tmp_path,
        {
            "fat1": ["Greedy", "Sorting"],
            "fat2": ["Greedy", "Sorting"],
            "thin": ["Trie", "Backtracking"],
        },
    )
    order = spread(attempts, problems, covered=Counter({"greedy": 40, "sorting": 40}))
    assert order[0].id == "a-thin"


def test_prior_coverage_does_not_drop_an_attempt(tmp_path):
    """It reorders the pool and never filters it: an attempt on a technique
    already claimed is later, not gone, or a sample cut long would be short."""
    attempts, problems = skewed(tmp_path, common=10)
    order = spread(attempts, problems, covered=Counter({"greedy": 99, "sorting": 99}))
    assert {one.id for one in order} == {one.id for one in attempts}


def test_no_prior_coverage_is_the_order_it_had(tmp_path):
    """The default is the current behaviour: an empty count is what `spread`
    starts from now, so nothing that does not pass one reads differently."""
    attempts, problems = skewed(tmp_path, common=20)
    assert [one.id for one in spread(attempts, problems, seed=3)] == [
        one.id for one in spread(attempts, problems, covered=Counter(), seed=3)
    ]


def test_claimable_levels_against_what_was_already_claimed(tmp_path):
    """The pool `claimable` returns has the hand-claimed attempts taken out of
    it, so the counts they carry have to reach `spread` some other way. Without
    that the batch is spread and the eval set it joins is not."""
    attempts, problems = pool(
        tmp_path,
        {
            "done1": ["Backtracking", "Greedy"],
            "done2": ["Backtracking", "Greedy"],
            "left1": ["Backtracking", "Greedy"],
            "left2": ["Trie", "Two Pointers"],
        },
    )
    # Tagged so the claimed technique sorts first: without prior coverage the
    # tie breaks on the code and `left1` leads, which is the current behaviour
    # and what this has to tell apart.
    claimed = {f"a-{id}": user_claim(f"a-{id}", ["greedy"]) for id in ("done1", "done2")}
    order = claimable(attempts, problems, claimed, user_id="u1")
    assert [one.id for one in order] == ["a-left2", "a-left1"]
