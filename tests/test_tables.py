from datetime import datetime
from enum import StrEnum
from typing import Any

import pytest
from pydantic import create_model
from sqlalchemy import Boolean, Column, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from tables import Stored, mismatches

from algo_coach.schema import MachineProvenance
from algo_coach.storage import enumerated, metadata, provenance_columns, timestamp

# every stored record and its table. Each store adds its own as its tables land
STORED: list[Stored] = []


@pytest.mark.parametrize("stored", STORED, ids=lambda one: one.table.name)
def test_a_table_holds_exactly_its_record_s_fields(stored):
    """The tables and the pydantic models are declared apart, and a field added
    to one alone is a value the copy loses or a column nothing writes."""
    assert mismatches(stored) == []


def test_every_table_is_declared_on_the_shared_metadata():
    """One metadata is what Alembic reads, so a table on another is a table no
    migration creates."""
    assert all(one.table.metadata is metadata for one in STORED)


def test_the_provenance_columns_are_the_fields_every_machine_record_inherits():
    table = Table("provenance", MetaData(), *provenance_columns())

    assert mismatches(Stored(MachineProvenance, table)) == []


# built by call rather than by a class statement: the dead-code check reports a
# member or a field nothing reads by name
Colour = StrEnum("Colour", {"RED": "red", "DARK_BLUE": "dark-blue"})


def test_an_enum_is_stored_by_its_values_under_a_snake_case_type():
    """A stored JSON record already carries the value, and the member name is a
    Python spelling the database has no use for."""
    kind = enumerated(Colour)

    assert (kind.name, list(kind.enums)) == ("colour", ["red", "dark-blue"])


def test_a_timestamp_keeps_its_time_zone():
    assert timestamp().timezone


Point = create_model("Point", x=(int, ...), y=(int | None, None))
Shape = create_model(
    "Shape",
    id=(str, ...),
    colour=(Colour, ...),
    drawn_at=(datetime, ...),
    closed=(bool, False),
    tags=(list[str], []),
    payload=(Any, ...),
    origin=(Point, ...),
    points=(list[Point], []),
)


def shape_table(*changes: Column[Any], without: tuple[str, ...] = ()) -> Table:
    columns = {
        one.name: one
        for one in (
            Column("id", Text, primary_key=True),
            Column("colour", enumerated(Colour), nullable=False),
            Column("drawn_at", timestamp(), nullable=False),
            Column("closed", Boolean, nullable=False),
            Column("tags", ARRAY(Text), nullable=False),
            Column("payload", JSONB, nullable=False),
            Column("origin_x", Integer, nullable=False),
            Column("origin_y", Integer),
        )
    }
    for name in without:
        del columns[name]
    columns |= {one.name: one for one in changes}
    return Table("shapes", MetaData(), *columns.values())


def shape(table: Table, **overrides) -> Stored:
    return Stored(Shape, table, **{"elsewhere": frozenset({"points"})} | overrides)


def test_a_table_matching_its_record_has_no_mismatch():
    """A nested record is prefixed columns, and a list of records is left to
    its child table."""
    assert mismatches(shape(shape_table())) == []


def test_a_field_without_a_column_is_reported():
    assert mismatches(shape(shape_table(without=("closed",)))) == [
        "shapes: no column for the field closed"
    ]


def test_a_column_without_a_field_is_reported():
    assert mismatches(shape(shape_table(Column("area", Integer)))) == ["shapes.area: no field"]


def test_a_structural_column_is_not_a_field():
    """A child table carries its parent's id and a position no record names."""
    table = shape_table(Column("position", Integer, nullable=False))

    assert mismatches(shape(table, structural=frozenset({"position"}))) == []


def test_a_nullability_the_field_does_not_allow_is_reported():
    table = shape_table(Column("closed", Boolean), Column("origin_y", Integer, nullable=False))

    assert mismatches(shape(table)) == [
        "shapes.closed: the field wants it NOT NULL",
        "shapes.origin_y: the field wants it nullable",
    ]


@pytest.mark.parametrize(
    ("column", "field"),
    [
        (Column("drawn_at", Text, nullable=False), "drawn_at"),
        (Column("colour", Text, nullable=False), "colour"),
        (Column("tags", JSONB, nullable=False), "tags"),
        (Column("payload", Text, nullable=False), "payload"),
    ],
)
def test_a_column_of_the_wrong_type_is_reported(column, field):
    """A string where the field is a timestamp, an enum or a list stores what
    the record's validator would refuse."""
    (found,) = mismatches(shape(shape_table(column)))

    assert found.startswith(f"shapes.{field}: ")


def test_an_enum_column_with_other_values_is_reported():
    Other = StrEnum("Other", {"RED": "red"})

    (found,) = mismatches(shape(shape_table(Column("colour", enumerated(Other), nullable=False))))

    assert found.startswith("shapes.colour: ")


def test_a_list_of_records_must_name_its_child_table():
    with pytest.raises(AssertionError, match="points is a list of records"):
        mismatches(Stored(Shape, shape_table()))
