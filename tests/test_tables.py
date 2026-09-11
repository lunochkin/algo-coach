from datetime import datetime
from enum import StrEnum
from typing import Any

import pytest
from pydantic import create_model
from sqlalchemy import Boolean, CheckConstraint, Column, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from tables import Stored, mismatches

from algo_coach.calls.table import calls
from algo_coach.problems.table import problems
from algo_coach.schema import (
    Call,
    ClaimSource,
    MachineProvenance,
    Problem,
    Solution,
    SolutionClaim,
)
from algo_coach.solution_claims.table import solution_claims
from algo_coach.solutions.table import solutions
from algo_coach.storage import call_column, enumerated, metadata, timestamp

# every stored record and its table. Each store adds its own as its tables land
STORED: list[Stored] = [
    Stored(Call, calls),
    Stored(
        Problem,
        problems,
        through_call=True,
        required=frozenset({"call_id"}),
        elsewhere=frozenset({"techniques"}),
    ),
    Stored(SolutionClaim, solution_claims, through_call=True),
    Stored(Solution, solutions, through_call=True, required=frozenset({"call_id"})),
]


@pytest.mark.parametrize("stored", STORED, ids=lambda one: one.table.name)
def test_a_table_holds_exactly_its_record_s_fields(stored):
    """The tables and the pydantic models are declared apart, and a field added
    to one alone is a value the copy loses or a column nothing writes."""
    assert mismatches(stored) == []


def test_every_table_is_declared_on_the_shared_metadata():
    """One metadata is what Alembic reads, so a table on another is a table no
    migration creates."""
    assert all(one.table.metadata is metadata for one in STORED)


def test_a_machine_record_holds_its_call_and_none_of_the_configuration():
    """`machine.md`: the configuration is stored once, on the call."""
    table = Table("provenance", MetaData(), call_column(nullable=True))

    assert mismatches(Stored(MachineProvenance, table, through_call=True)) == []


def test_the_call_column_references_the_calls_table():
    (key,) = call_column(nullable=False).foreign_keys

    assert key.target_fullname == "calls.id"


def test_a_copied_configuration_column_is_reported_on_a_machine_record():
    table = Table("provenance", MetaData(), call_column(nullable=True), Column("model", Text))

    assert mismatches(Stored(MachineProvenance, table, through_call=True)) == [
        "provenance.model: no field"
    ]


def test_a_field_the_validator_requires_is_a_not_null_column():
    """A generated problem always names its call, though a user's claim of the
    same shape does not."""
    table = Table("provenance", MetaData(), call_column(nullable=False))
    stored = Stored(MachineProvenance, table, through_call=True, required=frozenset({"call_id"}))

    assert mismatches(stored) == []
    assert mismatches(Stored(MachineProvenance, table, through_call=True)) == [
        "provenance.call_id: the field wants it nullable"
    ]


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


def test_a_call_is_refused_in_the_database_unless_it_answered_or_failed():
    """`Call` rejects both and neither, and a writer that skips the model meets
    the same rule in the table."""
    assert (
        checks(calls)["calls_answered_or_failed_check"] == "(response IS NULL) <> (error IS NULL)"
    )


def checks(table: Table) -> dict[str, str]:
    return {
        str(one.name): str(one.sqltext)
        for one in table.constraints
        if isinstance(one, CheckConstraint)
    }


def test_a_solution_claim_names_a_call_exactly_when_the_classifier_wrote_it():
    """A user's reading carries no provenance, and a machine's carries all of
    it, as `SolutionClaim` validates."""
    assert checks(solution_claims)["solution_claims_call_matches_source_check"] == (
        "(source = 'classifier') = (call_id IS NOT NULL)"
    )


def test_one_enum_is_one_postgres_type_however_many_tables_use_it():
    """A second declaration of the same type would have a migration create it
    twice."""
    assert enumerated(ClaimSource) is enumerated(ClaimSource)


def test_a_problem_s_rules_hold_in_the_table():
    """A problem names one target at most, and a retired one names why, as
    `Problem` validates."""
    held = checks(problems)

    assert held["problems_one_target_check"] == (
        "target_template_id IS NULL OR target_technique IS NULL"
    )
    assert held["problems_retirement_names_its_reason_check"] == (
        "(status = 'retired') = (retired_reason IS NOT NULL)"
    )
