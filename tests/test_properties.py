from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from algo_coach.runner import agrees, as_json
from algo_coach.standing import latest_by, standing
from algo_coach.storage import JsonlLog

json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda inner: st.lists(inner) | st.dictionaries(st.text(), inner),
    max_leaves=12,
)


@given(json_values)
def test_a_value_agrees_with_itself(value):
    assert agrees(value, value)


@given(st.lists(json_values))
def test_a_tuple_and_a_list_are_one_answer(items):
    """`corpus.md`: a case is decided by JSON equality, and JSON has no
    tuple."""
    assert agrees(tuple(items), items)


@given(st.dictionaries(st.text(), json_values, min_size=2))
def test_key_order_does_not_decide_a_case(mapping):
    """Encoded with sorted keys, so two dicts differing in insertion order are
    one answer."""
    reversed_order = dict(reversed(list(mapping.items())))
    assert agrees(mapping, reversed_order)
    assert as_json(mapping) == as_json(reversed_order)


def test_a_boolean_and_an_integer_are_two_answers():
    """`corpus.md`: `True` and `1` are two, where a tuple and a list are one."""
    assert not agrees(True, 1)
    assert not agrees(False, 0)


@dataclass(frozen=True)
class Stamped:
    key: str
    created_at: datetime
    source: str
    position: int  # append order, which nothing but the list carries


def stamped(source: str) -> st.SearchStrategy[list[Stamped]]:
    return st.lists(
        st.tuples(st.sampled_from("abc"), st.integers(0, 5)),
        max_size=12,
    ).map(
        lambda pairs: [
            Stamped(key, datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=days), source, at)
            for at, (key, days) in enumerate(pairs)
        ]
    )


@given(stamped("machine"))
def test_the_latest_record_stands_and_append_order_breaks_a_tie(records):
    """`log.md`: latest first, with append order breaking a tie."""
    stands = latest_by(records, lambda one: one.key)
    for key, record in stands.items():
        rivals = [one for one in records if one.key == key]
        assert record.created_at == max(one.created_at for one in rivals)
        assert record.position == max(
            one.position for one in rivals if one.created_at == record.created_at
        )


@given(stamped("machine"), stamped("user"))
def test_the_weaker_writer_never_stands_where_the_stronger_wrote(machine, user):
    """`README.md`: the user's record stands over the machine's, whichever was
    written later."""
    stands = standing([*machine, *user], lambda one: one.key, by_what_each_knew=("machine", "user"))
    for record in user:
        assert stands[record.key].source == "user"
    for key, record in stands.items():
        if record.source == "machine":
            assert not any(one.key == key for one in user)


class Line(BaseModel):
    n: int
    text: str


@given(st.lists(st.tuples(st.integers(), st.text()), max_size=20))
def test_a_log_reads_back_what_was_appended_in_order(tmp_path_factory, rows):
    """`storage`: append-only, read back in append order."""
    log = JsonlLog(tmp_path_factory.mktemp("log"), "lines.jsonl", Line)
    for n, text in rows:
        log.append(Line(n=n, text=text))
    assert [(one.n, one.text) for one in log.all()] == rows
