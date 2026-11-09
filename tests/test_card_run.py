from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from algo_coach.mint import card_run
from algo_coach.schema import CardRun, Probe

USER = "u-4f9c2a"
BEGAN = datetime(2026, 6, 1, tzinfo=UTC)


def test_a_run_carries_the_user_the_card_and_when_it_began():
    """The ladder is measured from the start, so the start is what the record
    exists to hold."""
    run = card_run(USER, "c-1", [], at=BEGAN)

    assert (run.user_id, run.card_id, run.started_at) == (USER, "c-1", BEGAN)
    assert run.id


def test_the_probes_the_start_drew_carry_the_start_s_moment():
    """A later probe reads as the later offer it is, which one moment per
    probe is what says."""
    run = card_run(USER, "c-1", ["p-1", "p-2"], at=BEGAN)

    assert [(one.problem_id, one.assigned_at) for one in run.probes] == [
        ("p-1", BEGAN),
        ("p-2", BEGAN),
    ]


def test_a_later_probe_appends():
    """What was offered and when stays readable, so a second offer joins the
    first rather than replacing it."""
    run = card_run(USER, "c-1", ["p-1"], at=BEGAN)
    later = BEGAN + timedelta(days=3)

    grown = run.model_copy(
        update={"probes": [*run.probes, Probe(problem_id="p-2", assigned_at=later)]}
    )

    assert [(one.problem_id, one.assigned_at) for one in grown.probes] == [
        ("p-1", BEGAN),
        ("p-2", later),
    ]


def test_a_probe_before_the_start_is_refused():
    """The run is what a probe is offered on, so no probe predates it."""
    with pytest.raises(ValidationError, match="assigned at the start or after"):
        CardRun(
            id="r-1",
            user_id=USER,
            card_id="c-1",
            started_at=BEGAN,
            probes=[Probe(problem_id="p-1", assigned_at=BEGAN - timedelta(days=1))],
        )


def test_one_probe_per_problem():
    """A problem offered twice tests no recognition the first offer did
    not."""
    with pytest.raises(ValidationError, match="once"):
        CardRun(
            id="r-1",
            user_id=USER,
            card_id="c-1",
            started_at=BEGAN,
            probes=[
                Probe(problem_id="p-1", assigned_at=BEGAN),
                Probe(problem_id="p-1", assigned_at=BEGAN + timedelta(days=1)),
            ],
        )


def test_a_run_needs_no_probe():
    """A card whose corpus offers nothing unseen still starts, and the ladder
    is what the start measures."""
    assert card_run(USER, "c-1", []).probes == []
