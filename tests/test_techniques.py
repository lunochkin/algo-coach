import json
from importlib import resources

from algo_coach.schema import Technique
from algo_coach.techniques import codes, is_known


def raw_list() -> list[str]:
    text = resources.files("algo_coach.techniques").joinpath("vocabulary.json").read_text()
    return json.loads(text)["techniques"]


def test_vocabulary_is_not_empty():
    assert codes()


def test_every_code_is_a_slug():
    for code in codes():
        assert Technique(code=code).code == code


def test_no_duplicates():
    entries = raw_list()
    assert len(entries) == len(set(entries))


def test_file_stays_sorted():
    """Sorted on disk so a new technique is a one-line diff, not a reshuffle."""
    entries = raw_list()
    assert entries == sorted(entries)


def test_is_known():
    assert is_known("backtracking")
    assert not is_known("not-a-technique")


def test_is_known_does_not_reject_retired_codes_at_read_time():
    """The vocabulary gates writes. Reading a record must never consult it —
    this test pins the seam, so a retired code cannot break the log."""
    assert not is_known("retired-code")
    assert Technique(code="retired-code").code == "retired-code"
