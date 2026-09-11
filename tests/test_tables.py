import sys
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import pytest
from pydantic import create_model
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from tables import Stored, mismatches
from test_schema_additive import RECORDS

import algo_coach
from algo_coach.calls.table import calls
from algo_coach.cards.table import card_templates, cards
from algo_coach.cases.table import test_cases
from algo_coach.drafts.table import (
    SettledField,
    draft_declared_cases,
    draft_settled_cases,
    drafts,
)
from algo_coach.log.table import (
    attempt_claims,
    attempt_verification_case_results,
    attempt_verifications,
    attempts,
    diagnoses,
    self_labels,
    sitting_pauses,
    sittings,
    users,
)
from algo_coach.matches.table import template_matches
from algo_coach.outcomes.table import site_outcomes
from algo_coach.problems.table import problems
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    AttemptVerification,
    Call,
    CallSite,
    Card,
    CaseResult,
    ClaimSource,
    Diagnosis,
    Draft,
    DraftCase,
    MachineProvenance,
    Pause,
    Problem,
    SelfLabel,
    SettledCase,
    SiteOutcome,
    Sitting,
    Solution,
    SolutionClaim,
    Template,
    TemplateMatch,
    TestCase,
    Verification,
)
from algo_coach.solution_claims.table import solution_claims
from algo_coach.solutions.table import solutions
from algo_coach.storage import call_column, enumerated, metadata, timestamp
from algo_coach.verifications.table import verification_case_results, verifications

# every stored record and its table. Each store adds its own as its tables land
STORED: list[Stored] = [
    Stored(Attempt, attempts),
    Stored(AttemptClaim, attempt_claims, through_call=True),
    Stored(SelfLabel, self_labels),
    Stored(Diagnosis, diagnoses, through_call=True, required=frozenset({"call_id"})),
    Stored(AttemptVerification, attempt_verifications, elsewhere=frozenset({"results"})),
    Stored(
        CaseResult,
        attempt_verification_case_results,
        structural=frozenset({"attempt_verification_id", "position"}),
    ),
    Stored(Call, calls),
    Stored(
        Draft,
        drafts,
        elsewhere=frozenset(
            {
                "declared",
                "cases",
                "kept",
                "won",
                "separating_case",
                *(f"{site}_provenance" for site in CallSite),
            }
        ),
        structural=frozenset(f"{site}_call_id" for site in CallSite),
    ),
    Stored(DraftCase, draft_declared_cases, structural=frozenset({"draft_id", "position"})),
    Stored(
        SettledCase,
        draft_settled_cases,
        structural=frozenset({"draft_id", "draft_field", "position", "call_id"}),
        elsewhere=frozenset({"provenance"}),
    ),
    Stored(TestCase, test_cases, through_call=True, required=frozenset({"call_id"})),
    Stored(Card, cards, elsewhere=frozenset({"templates"})),
    Stored(Template, card_templates, structural=frozenset({"card_id", "position"})),
    Stored(
        Problem,
        problems,
        through_call=True,
        required=frozenset({"call_id"}),
        elsewhere=frozenset({"techniques"}),
    ),
    Stored(SolutionClaim, solution_claims, through_call=True),
    Stored(TemplateMatch, template_matches, through_call=True),
    Stored(SiteOutcome, site_outcomes, through_call=True, required=frozenset({"call_id"})),
    Stored(Sitting, sittings, elsewhere=frozenset({"pauses"})),
    Stored(Pause, sitting_pauses, structural=frozenset({"sitting_id", "position"})),
    Stored(Verification, verifications, elsewhere=frozenset({"results"})),
    Stored(
        CaseResult,
        verification_case_results,
        structural=frozenset({"verification_id", "position"}),
    ),
    Stored(Solution, solutions, through_call=True, required=frozenset({"call_id"})),
]


@pytest.mark.parametrize("stored", STORED, ids=lambda one: one.table.name)
def test_a_table_holds_exactly_its_record_s_fields(stored):
    """The tables and the pydantic models are declared apart, and a field added
    to one alone is a value the copy loses or a column nothing writes."""
    assert mismatches(stored) == []


# the tables no record is stored in whole: the user is an id the records
# reference, before any account fills it
WITHOUT_A_RECORD = {"users"}


def test_every_stored_record_has_a_table():
    """A record left without one is a store the copy to Postgres skips."""
    tabled = {one.record for one in STORED}

    assert [one.__name__ for one in RECORDS if one not in tabled] == []


def test_every_table_module_is_imported_here():
    """A table module this file never imports puts no table on the metadata
    the checks below read."""
    source = Path(algo_coach.__file__).parent
    declared = {
        ".".join(("algo_coach", *path.relative_to(source).with_suffix("").parts))
        for path in source.rglob("table.py")
    }

    assert sorted(declared - set(sys.modules)) == []


def test_every_table_is_compared_with_its_record():
    """A table no record is compared with is one a field can leave behind
    unnoticed."""
    compared = {one.table.name for one in STORED} | WITHOUT_A_RECORD

    assert sorted(set(metadata.tables) - compared) == []


def test_every_foreign_key_names_a_declared_table():
    """A reference to a table nobody declared fails only when the migration
    creates the tables, far from the table that named it."""
    unresolved = [
        f"{key.parent.table.name}.{key.parent.name} -> {key.target_fullname}"
        for table in metadata.tables.values()
        for key in table.foreign_keys
        if key.column.table.name not in metadata.tables
    ]

    assert unresolved == []


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


def test_a_card_holds_one_optional_template_at_most():
    """`Card` rejects a second one, and the index refuses it in the table."""
    (index,) = [
        one for one in card_templates.indexes if one.name == "card_templates_one_optional_idx"
    ]

    assert index.unique and str(index.dialect_options["postgresql"]["where"]) == "optional"


def test_a_template_slug_is_unique_within_its_card():
    """A re-seed matches a template by its slug, so two of one slug leave no
    rule for which id to keep."""
    keys = {
        tuple(column.name for column in one.columns)
        for one in card_templates.constraints
        if isinstance(one, UniqueConstraint)
    }

    assert ("card_id", "slug") in keys


def test_a_match_names_a_call_only_where_the_matcher_wrote_it():
    """A generator's match is an assertion and a user's a reading, and neither
    carries provenance, as `TemplateMatch` validates."""
    assert checks(template_matches)["template_matches_call_matches_source_check"] == (
        "(source = 'classifier') = (call_id IS NOT NULL)"
    )


def test_a_case_s_expected_null_is_a_value_the_column_keeps():
    """`None` is a return a solution may give, so absence cannot stand in for
    it, and the JSONB column stores it as JSON `null` rather than SQL NULL."""
    assert test_cases.c.expected.type.none_as_null is False
    assert not test_cases.c.expected.nullable


def test_a_case_s_arguments_are_a_json_array():
    """The arguments are positional, and anything but an array reaches `solve`
    as one argument."""
    assert checks(test_cases)["test_cases_args_positional_check"] == "jsonb_typeof(args) = 'array'"


def test_a_site_outcome_names_one_target_at_most():
    """As on the draft and the problem, a writing had one target."""
    assert checks(site_outcomes)["site_outcomes_one_target_check"] == (
        "target_template_id IS NULL OR target_technique IS NULL"
    )


def test_an_outcome_s_writing_id_is_not_a_foreign_key():
    """A landing clears the draft the writing id names, and a replay's writing
    never had one."""
    assert not site_outcomes.c.writing_id.foreign_keys


def test_a_case_result_s_rules_hold_in_the_table():
    """A value the child returned was timed, and only a crash names what raised,
    as `CaseResult` validates."""
    held = checks(verification_case_results)

    assert held["verification_case_results_returned_was_timed_check"] == (
        "outcome NOT IN ('passed', 'wrong') OR elapsed_ms IS NOT NULL"
    )
    assert held["verification_case_results_only_a_crash_names_an_error_check"] == (
        "error IS NULL OR outcome = 'crashed'"
    )


def test_every_list_of_settled_cases_is_a_draft_field():
    """A row names the list it belongs to by the draft's own field name."""
    assert {one.value for one in SettledField} <= set(Draft.model_fields)


def test_a_draft_names_the_call_of_each_of_its_five_sites():
    """The configuration a resume compares is on the call, so a site's
    provenance is one reference, absent where the site has not run."""
    assert {one.value for one in CallSite} == {
        name.removesuffix("_provenance")
        for name in Draft.model_fields
        if name.endswith("_provenance")
    }
    for site in CallSite:
        column = drafts.c[f"{site}_call_id"]
        (key,) = column.foreign_keys
        assert (key.target_fullname, column.nullable) == ("calls.id", True)
    assert not draft_settled_cases.c.call_id.nullable


def test_what_a_draft_held_goes_with_it():
    """A landing clears the draft, and its cases have nothing left to belong
    to."""
    for child in (draft_declared_cases, draft_settled_cases):
        (key,) = child.c.draft_id.foreign_keys
        assert key.ondelete == "CASCADE"


def test_a_draft_s_rules_hold_in_the_table():
    held = checks(drafts)

    assert (
        held["drafts_rejection_names_its_gate_check"] == "(state = 'rejected') = (gate IS NOT NULL)"
    )
    assert held["drafts_landing_names_the_problem_check"] == (
        "(state = 'landed') = (problem_id IS NOT NULL)"
    )
    assert held["drafts_input_generator_carries_its_bound_check"] == (
        "(input_generator IS NULL) = (largest IS NULL)"
    )


def test_a_user_is_the_engine_s_own_id_and_nothing_of_an_account():
    """A private record's `user_id` references this row, and a provider switch
    would otherwise rewrite the log: `README.md`."""
    assert [one.name for one in users.columns] == ["id", "created_at"]
    assert users.c.id.primary_key and not users.c.created_at.nullable


def test_an_attempt_references_its_user_problem_and_sitting():
    """Every reference in an append-only record is engine-minted, and the table
    refuses one that names nothing: `README.md`."""
    targets = {
        column.name: key.target_fullname
        for column in attempts.columns
        for key in column.foreign_keys
    }

    assert targets == {
        "user_id": "users.id",
        "problem_id": "problems.id",
        "sitting_id": "sittings.id",
    }


def test_one_sitting_runs_on_a_problem_for_a_user():
    """A refresh or a second tab reaches the clock already running, so the table
    refuses a second one."""
    (index,) = [one for one in sittings.indexes if one.name == "sittings_one_running_idx"]

    assert index.unique
    assert [column.name for column in index.columns] == ["user_id", "problem_id"]
    assert str(index.dialect_options["postgresql"]["where"]) == "ended_at IS NULL"


def test_an_attempt_s_case_results_hold_the_rules_a_solution_s_do():
    """The two tables are declared apart, so a rule added to one alone judges
    the same result two ways."""

    def rules(table: Table) -> set[str]:
        prefix = f"{table.name}_"
        return {f"{name.removeprefix(prefix)}={sql}" for name, sql in checks(table).items()}

    assert rules(attempt_verification_case_results) == rules(verification_case_results)


def test_an_attempt_claim_s_rules_hold_in_the_table():
    """A user names a technique or declines, and a decline names nothing, as
    `AttemptClaim` validates: an empty user claim would make a lost answer and
    a stated verdict one row."""
    held = checks(attempt_claims)

    assert held["attempt_claims_user_claim_answers_check"] == (
        "source <> 'user' OR cardinality(techniques) > 0 OR declined"
    )
    assert held["attempt_claims_decline_names_nothing_check"] == (
        "NOT (cardinality(techniques) > 0 AND declined)"
    )
    assert held["attempt_claims_call_matches_source_check"] == (
        "(source = 'classifier') = (call_id IS NOT NULL)"
    )


def test_every_record_keyed_to_an_attempt_references_it():
    """`README.md`: a record keyed to an attempt carries its `attempt_id`, and
    the table refuses one naming no attempt."""
    for table in (attempt_verifications, attempt_claims, self_labels, diagnoses):
        (key,) = table.c.attempt_id.foreign_keys
        assert key.target_fullname == "attempts.id"
