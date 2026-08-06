from helpers import attempt, machine_claim, seed_problem

from algo_coach.board import movement
from algo_coach.problems import ProblemStore


def problems(root):
    return {problem.id: problem for problem in ProblemStore(root).all()}


def claim(attempt_id: str, *techniques: str):
    return machine_claim(attempt_id, list(techniques))


def rows(result):
    return {row.technique: row for row in result}


def test_a_narrowed_claim_takes_credit_off_the_other_tag(tmp_path):
    """The fallback credits both tags; the claim credits one, and the board is
    read per technique, so the difference is where practice gets steered."""
    seed_problem(tmp_path, id="two-tags", tags=["Greedy", "Sorting"])
    one = attempt("a1", "two-tags")
    claims = {"a1": claim("a1", "greedy")}

    result = rows(movement([one], problems(tmp_path), claims))

    assert (result["greedy"].fallback, result["greedy"].claimed) == (1, 1)
    assert (result["sorting"].fallback, result["sorting"].claimed) == (1, 0)
    assert result["sorting"].moved == -1


def test_a_claim_naming_every_candidate_moves_nothing(tmp_path):
    """The hedge the check exists to catch: it agrees with the tags, decides
    nothing, and would still write a claim for every attempt."""
    seed_problem(tmp_path, id="two-tags", tags=["Greedy", "Sorting"])
    one = attempt("a1", "two-tags")
    claims = {"a1": claim("a1", "greedy", "sorting")}

    result = movement([one], problems(tmp_path), claims)

    assert all(row.moved == 0 for row in result)


def test_an_unclaimed_attempt_moves_nothing(tmp_path):
    seed_problem(tmp_path, id="two-tags", tags=["Greedy", "Sorting"])

    result = movement([attempt("a1", "two-tags")], problems(tmp_path), {})

    assert all(row.moved == 0 for row in result)


def test_a_single_tag_problem_cannot_move(tmp_path):
    """Nothing to narrow: the fallback already names one code."""
    seed_problem(tmp_path, id="one-tag", tags=["Trie"])
    one = attempt("a1", "one-tag")

    result = rows(movement([one], problems(tmp_path), {"a1": claim("a1", "trie")}))

    assert (result["trie"].fallback, result["trie"].claimed, result["trie"].moved) == (1, 1, 0)


def test_a_technique_the_claims_emptied_still_gets_a_row(tmp_path):
    """A code narrowed away everywhere is exactly the one worth seeing."""
    seed_problem(tmp_path, id="two-tags", tags=["Greedy", "Sorting"])
    one = attempt("a1", "two-tags")

    result = rows(movement([one], problems(tmp_path), {"a1": claim("a1", "greedy")}))

    assert result["sorting"].claimed == 0


def test_the_rows_are_ordered_by_technique(tmp_path):
    seed_problem(tmp_path, id="two-tags", tags=["Greedy", "Sorting"])

    result = movement([attempt("a1", "two-tags")], problems(tmp_path), {})

    assert [row.technique for row in result] == ["greedy", "sorting"]
