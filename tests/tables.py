"""Comparing a Postgres table with the record it stores. The two are declared
apart, so this is what keeps them equal."""

import types
import typing
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String, Table
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from algo_coach.schema import MachineProvenance


@dataclass(frozen=True)
class Stored:
    record: type[BaseModel]
    table: Table
    # columns the table adds for its own structure: a parent's id, a position
    structural: frozenset[str] = field(default_factory=frozenset)
    # fields held somewhere other than this table's columns: a list of records
    # in its child table, or a derived view no store writes
    elsewhere: frozenset[str] = field(default_factory=frozenset)
    # a machine record: the configuration is read from the call its `call_id`
    # names, so the table holds none of it
    through_call: bool = False
    # optional in the annotation and required by the record's validator, so the
    # column is NOT NULL
    required: frozenset[str] = field(default_factory=frozenset)


def mismatches(stored: Stored) -> list[str]:
    name = stored.table.name
    configuration = frozenset(MachineProvenance.model_fields) - {"call_id"}
    expected = _expected(
        stored.record, stored.elsewhere | (configuration if stored.through_call else frozenset())
    )
    for one in stored.required:
        expected[one] = (expected[one][0], False)
    actual = {one.name: one for one in stored.table.columns if one.name not in stored.structural}
    found = [
        f"{name}: no column for the field {one}" for one in sorted(expected.keys() - actual.keys())
    ]
    found += [f"{name}.{one}: no field" for one in sorted(actual.keys() - expected.keys())]
    for column_name in sorted(expected.keys() & actual.keys()):
        annotation, nullable = expected[column_name]
        column = actual[column_name]
        if column.nullable != nullable:
            wanted = "nullable" if nullable else "NOT NULL"
            found.append(f"{name}.{column_name}: the field wants it {wanted}")
        if not _typed(column, annotation):
            found.append(f"{name}.{column_name}: {column.type!r} does not hold {annotation!r}")
    return found


def _expected(
    record: type[BaseModel], elsewhere: frozenset[str], prefix: str = ""
) -> dict[str, tuple[object, bool]]:
    columns: dict[str, tuple[object, bool]] = {}
    for field_name, info in record.model_fields.items():
        if field_name in elsewhere:
            continue
        inner, nullable = _unwrapped(info.annotation)
        if _is_model(inner):
            # one nested record is its own columns, prefixed by the field
            for column_name, (annotation, inner_nullable) in _expected(
                inner, frozenset(), f"{prefix}{field_name}_"
            ).items():
                columns[column_name] = (annotation, inner_nullable or nullable)
            continue
        if typing.get_origin(inner) is list and _is_model(typing.get_args(inner)[0]):
            raise AssertionError(
                f"{record.__name__}.{field_name} is a list of records: name it in `elsewhere`, "
                "and compare its child table on its own"
            )
        columns[f"{prefix}{field_name}"] = (inner, nullable)
    return columns


def _unwrapped(annotation: object) -> tuple[object, bool]:
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        rest = [one for one in typing.get_args(annotation) if one is not type(None)]
        nullable = len(rest) < len(typing.get_args(annotation))
        return (rest[0] if len(rest) == 1 else annotation), nullable
    return annotation, False


def _is_model(annotation: object) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def _typed(column: Column[Any], annotation: object) -> bool:
    kind = column.type
    if annotation is Any:
        # JSON of any shape: a stored `null` is a value, so NOT NULL still holds
        return isinstance(kind, JSONB)
    if typing.get_origin(annotation) is list:
        (item,) = typing.get_args(annotation)
        if item is Any:
            return isinstance(kind, JSONB)
        return isinstance(kind, ARRAY) and _typed(Column("item", kind.item_type), item)
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return isinstance(kind, Enum) and list(kind.enums) == [
            member.value for member in annotation
        ]
    if annotation is bool:
        return isinstance(kind, Boolean)
    if annotation is int:
        return isinstance(kind, Integer)
    if annotation is float:
        return isinstance(kind, Float)
    if annotation is str:
        return isinstance(kind, String) and not isinstance(kind, Enum)
    if annotation is datetime:
        return isinstance(kind, DateTime) and kind.timezone
    return False
