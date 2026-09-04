from helpers import PROVENANCE, a_call

from algo_coach.drafts import DraftStore
from algo_coach.schema import Discard, Draft, ExpectedSource, WritingState

CONTENT = {
    "title": "Two Sum",
    "statement": "Given an array, return ...",
    "canonical": "def solve(xs):\n    return len(xs)\n",
    "declared": [{"args": [[1, 2]], "expected": 2}],
    "difficulty": "easy",
}


def make_draft(id: str = "w1", **overrides) -> Draft:
    return Draft.model_validate(CONTENT | {"id": id} | overrides)


def test_put_and_get(tmp_path):
    store = DraftStore(tmp_path)
    draft = make_draft()
    store.put(draft)

    assert store.get("w1") == draft


def test_get_missing_is_none(tmp_path):
    assert DraftStore(tmp_path).get("nope") is None


def test_a_draft_is_revised_in_place(tmp_path):
    """Working state rather than a log: a step's answer moves the draft it was
    written on, where every other store appends a second record."""
    store = DraftStore(tmp_path)
    store.put(make_draft())
    store.put(make_draft(state=WritingState.REFERENCED, reference="def solve(xs): ..."))

    assert store.get("w1").state is WritingState.REFERENCED
    assert len(store.all()) == 1


def test_what_a_step_left_reads_back_whole(tmp_path):
    """A resume reads the outputs and the configurations off the file, so a
    round trip that dropped either would re-run a step that answered."""
    store = DraftStore(tmp_path)
    draft = make_draft(
        state=WritingState.HARDENED,
        reference="def solve(xs): ...",
        cases=[
            {
                "args": [[1, 2]],
                "expected": 2,
                "expected_from": "reference",
                "call": a_call().model_dump(mode="json"),
            }
        ],
        builder="def solve(size, seed): ...",
        largest=1000,
        generator=PROVENANCE,
    )
    store.put(draft)

    read = store.get("w1")

    assert read == draft
    assert read.cases[0].expected_from is ExpectedSource.REFERENCE
    assert read.generator.call_id == "call-1"


def test_a_rejected_draft_reads_back_with_its_gate(tmp_path):
    """Terminal means no resume rather than no record: what the gate said is
    the whole of what the attempt left."""
    store = DraftStore(tmp_path)
    store.put(make_draft(state=WritingState.REJECTED, gate=Discard.DISAGREED))

    assert store.get("w1").gate is Discard.DISAGREED


def test_drafts_are_read_in_id_order(tmp_path):
    store = DraftStore(tmp_path)
    for id in ("w2", "w1"):
        store.put(make_draft(id))

    assert [draft.id for draft in store.all()] == ["w1", "w2"]


def test_all_on_empty_store(tmp_path):
    assert DraftStore(tmp_path).all() == []


def test_a_cleared_draft_is_gone(tmp_path):
    """Landing is what clears one: the problem is stored, so the draft it was
    written through has nothing left to resume."""
    store = DraftStore(tmp_path)
    store.put(make_draft())
    store.remove("w1")

    assert store.get("w1") is None
    assert store.all() == []


def test_clearing_a_draft_that_is_gone_is_not_an_error(tmp_path):
    """A run that died between landing and clearing leaves the next one this
    to do, and a second clear must not stop it."""
    DraftStore(tmp_path).remove("nope")
