from helpers import PROVENANCE_FIELDS, a_call

from algo_coach.calls import CallLog
from algo_coach.drafts import DraftStore
from algo_coach.schema import Draft, ExpectedSource, Gate, WritingState

CONTENT = {
    "title": "Two Sum",
    "statement": "Given an array, return ...",
    "canonical": "def solve(xs):\n    return len(xs)\n",
    "declared": [{"args": [[1, 2]], "expected": 2}],
    "difficulty": "easy",
}


def make_draft(id: str = "w1", **overrides) -> Draft:
    return Draft.model_validate(CONTENT | {"id": id} | overrides)


def test_put_and_get(database):
    store = DraftStore(database)
    draft = make_draft()
    store.put(draft)

    assert store.get("w1") == draft


def test_get_missing_is_none(database):
    assert DraftStore(database).get("nope") is None


def test_a_draft_is_revised_in_place(database):
    """Working state rather than a log: a step's answer moves the draft it was
    written on, where every other store appends a second record."""
    store = DraftStore(database)
    store.put(make_draft())
    store.put(make_draft(state=WritingState.REFERENCED, reference="def solve(xs): ..."))

    assert store.get("w1").state is WritingState.REFERENCED
    assert len(store.all()) == 1


def test_what_a_step_left_reads_back_whole(database):
    """A resume reads the outputs and the configurations off the file, so a
    round trip that dropped either would re-run a step that answered."""
    store = DraftStore(database)
    draft = make_draft(
        state=WritingState.HARDENED,
        reference="def solve(xs): ...",
        cases=[
            {
                "args": [[1, 2]],
                "expected": 2,
                "expected_from": "reference",
                "provenance": PROVENANCE_FIELDS,
            }
        ],
        input_generator="def solve(size, seed): ...",
        largest=1000,
        generator_provenance=PROVENANCE_FIELDS,
    )
    store.put(draft)

    read = store.get("w1")

    assert read == draft
    assert read.cases[0].expected_from is ExpectedSource.REFERENCE
    assert read.generator_provenance.call_id == "call-1"


def test_a_rejected_draft_reads_back_with_its_gate(database):
    """Terminal means no resume rather than no record: what the gate said is
    the whole of what the attempt left."""
    store = DraftStore(database)
    store.put(make_draft(state=WritingState.REJECTED, gate=Gate.DISAGREED))

    assert store.get("w1").gate is Gate.DISAGREED


def test_drafts_are_read_in_id_order(database):
    store = DraftStore(database)
    for id in ("w2", "w1"):
        store.put(make_draft(id))

    assert [draft.id for draft in store.all()] == ["w1", "w2"]


def test_all_on_empty_store(database):
    assert DraftStore(database).all() == []


def test_a_cleared_draft_is_gone(database):
    """Landing is what clears one: the problem is stored, so the draft it was
    written through has nothing left to resume."""
    store = DraftStore(database)
    store.put(make_draft())
    store.remove("w1")

    assert store.get("w1") is None
    assert store.all() == []


def test_clearing_a_draft_that_is_gone_is_not_an_error(database):
    """A run that died between landing and clearing leaves the next one this
    to do, and a second clear must not stop it."""
    DraftStore(database).remove("nope")


def settled(args, expected, **overrides) -> dict:
    return {
        "args": args,
        "expected": expected,
        "expected_from": ExpectedSource.REFERENCE,
        "provenance": PROVENANCE_FIELDS,
    } | overrides


def test_a_whole_draft_reads_back_as_it_was_put(database):
    """Every list a run settles and every site's call land in their own rows,
    and a draft read back is the draft that was put."""
    CallLog(database).append(a_call("blind-call", temperature=0.0, provider=None))
    blind = PROVENANCE_FIELDS | {"call_id": "blind-call", "temperature": 0.0}
    draft = make_draft(
        state=WritingState.HARDENED,
        reference="def solve(xs):\n    return sum(1 for _ in xs)\n",
        input_generator="def build(size, seed): ...",
        largest=100_000,
        declared=[{"args": [[1, 2]], "expected": 2}, {"args": [[]], "expected": None}],
        cases=[settled([[1, 2]], 2), settled([[]], 0, expected_from=ExpectedSource.CANONICAL)],
        kept=[settled([[5]], 1, round=0)],
        won=[settled([[7, 7]], 2, round=1), settled([[9]], 1, round=2)],
        separating_case=settled([list(range(50))], 50, round=None, repeats=4),
        generator_provenance=PROVENANCE_FIELDS,
        blind_provenance=blind,
    )
    store = DraftStore(database)

    store.put(draft)

    assert store.get("w1") == draft


def test_a_revised_draft_holds_only_its_latest_cases(database):
    """A put replaces every case the draft held, so a list a step shortened
    reads back shorter."""
    store = DraftStore(database)
    store.put(make_draft(cases=[settled([[1]], 1), settled([[2]], 2)]))

    store.put(make_draft(cases=[settled([[3]], 3)]))

    assert [one.args for one in store.get("w1").cases] == [[[3]]]
