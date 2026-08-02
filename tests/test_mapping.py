import pytest

from algo_coach.techniques import aliases, codes, map_tags, normalise


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("Dynamic Programming", "dynamic-programming"),
        ("  two pointers  ", "two-pointers"),
        ("Bit_Manipulation", "bit-manipulation"),
        ("Breadth-First Search", "breadth-first-search"),
    ],
)
def test_normalisation_reaches_most_tags(tag, expected):
    assert map_tags([tag]) == [expected]


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("DFS", "depth-first-search"), ("DP", "dynamic-programming")],
)
def test_aliases_cover_what_normalisation_misses(tag, expected):
    assert map_tags([tag]) == [expected]


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("Tree", "tree-traversal"),
        ("Binary Tree", "binary-tree"),
        ("Binary Search Tree", "binary-search-tree"),
    ],
)
def test_tree_tags_reach_a_code(tag, expected):
    """A bare "Tree" says only that one is walked; the other two are their own
    techniques, and grouping them under traversal would credit it for the
    ordering invariant."""
    assert map_tags([tag]) == [expected]


def test_unmapped_tag_produces_no_code():
    assert map_tags(["Simulation", "Brainteaser"]) == []


@pytest.mark.parametrize("tag", ["Database", "Pandas", "Shell", "Interactive"])
def test_non_algorithmic_tags_stay_unmapped(tag):
    """Nothing about them is a technique to practise. Unmapped is the correct
    answer, not a gap to close later."""
    assert map_tags([tag]) == []


def test_unmapped_tags_do_not_block_the_rest():
    assert map_tags(["Simulation", "Greedy"]) == ["greedy"]


def test_result_is_deduplicated_and_sorted():
    assert map_tags(["DP", "Dynamic Programming", "Greedy"]) == [
        "dynamic-programming",
        "greedy",
    ]


def test_order_of_tags_does_not_change_the_result():
    assert map_tags(["Greedy", "Trie"]) == map_tags(["Trie", "Greedy"])


def test_empty_tags():
    assert map_tags([]) == []


def test_every_alias_target_is_a_known_code():
    """An alias pointing outside the vocabulary would silently drop tags."""
    assert set(aliases().values()) <= codes()


def test_no_alias_shadows_a_code():
    """A key that is already a code makes the alias unreachable, or worse,
    redirects a valid code somewhere else."""
    assert not set(aliases()) & codes()


def test_normalise_is_idempotent():
    for code in codes():
        assert normalise(code) == code
