import json
import re
from importlib import resources

import pytest
from helpers import PROVENANCE

from algo_coach.mint import user_claim
from algo_coach.schema import (
    Kind,
    Problem,
    Technique,
    TechniqueClaim,
)
from algo_coach.techniques import codes, criteria, is_known


def raw_list() -> list[dict]:
    text = resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    return json.loads(text)["techniques"]


def test_vocabulary_is_not_empty():
    assert codes()


def test_every_code_is_a_slug():
    for code in codes():
        assert criteria()[code].code == code


def test_no_duplicates():
    entries = [entry["code"] for entry in raw_list()]
    assert len(entries) == len(set(entries))


def test_file_stays_sorted():
    """Sorted on disk so a new technique is one hunk, not a reshuffle."""
    entries = [entry["code"] for entry in raw_list()]
    assert entries == sorted(entries)


def test_every_code_carries_its_criterion():
    """A code with a name and nothing else is what the classifier had, and the
    kinds it confused are the disagreements it produced."""
    for code, entry in criteria().items():
        assert entry.code == code
        assert entry.kind in Kind
        assert entry.earns.strip()
        assert entry.near_miss.strip()


def test_a_criterion_needs_all_three():
    for missing in ("kind", "earns", "near_miss"):
        entry = {
            "code": "example",
            "kind": Kind.PROCEDURE,
            "earns": "e",
            "near_miss": "n",
        }
        del entry[missing]
        with pytest.raises(ValueError):
            Technique.model_validate(entry)


def test_a_criterion_is_one_of_four_kinds():
    with pytest.raises(ValueError):
        Technique.model_validate(
            {"code": "example", "kind": "heuristic", "earns": "e", "near_miss": "n"}
        )


def test_every_kind_is_used():
    """Four kinds because one question is answered four ways. A kind nothing
    carries is a distinction the rulebook asserts and never applies."""
    assert {entry.kind for entry in criteria().values()} == set(Kind)


def test_a_cross_reference_names_a_code_that_exists():
    """A near miss sends the reader to the code that does cover it. Backticked
    because the reader is a model as often as a person, and a dangling one
    points at a claim nothing can make."""
    for entry in criteria().values():
        for referenced in re.findall(r"`([a-z0-9-]+)`", f"{entry.earns} {entry.near_miss}"):
            assert referenced in criteria()
            assert referenced != entry.code


def test_criteria_cannot_be_edited_in_place():
    """They reach a prompt and a reader unchanged: a mutable rulebook makes a
    reading whose criteria nothing recorded."""
    with pytest.raises(TypeError):
        criteria()["backtracking"] = criteria()["greedy"]


def test_is_known():
    assert is_known("backtracking")
    assert not is_known("not-a-technique")


def test_is_known_does_not_reject_retired_codes_at_read_time():
    """The vocabulary gates writes. Reading a record must never consult it —
    this test pins the seam, so a retired code cannot break the log.

    Pinned on the records themselves rather than on a model standing in for a
    code: a code in the log is a bare string, and a retired one has no
    vocabulary entry left to validate against.
    """
    retired = "retired-code"
    assert not is_known(retired)
    assert retired not in criteria()

    problem = Problem(
        id="p1",
        title="t",
        statement="s",
        techniques=[retired],
        **PROVENANCE,
    )
    assert Problem.model_validate_json(problem.model_dump_json()).techniques == [retired]

    claim = user_claim("a1", [retired])
    assert TechniqueClaim.model_validate_json(claim.model_dump_json()).techniques == [retired]


def test_every_kind_names_its_test():
    """The kind selects the question asked of a code, so a kind that cannot
    say what it selects is a label the prompt and the reader both guess at."""
    for kind in Kind:
        assert kind.test.strip()
    assert len({kind.test for kind in Kind}) == len(Kind)
