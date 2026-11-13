from datetime import UTC, datetime

from matching import card as card_record
from matching import seeded
from matching import template as template_record

from algo_coach.judgements import ItemStore
from algo_coach.judging import build, digest, items, shown
from algo_coach.judging.build import WIDTH
from algo_coach.schema import Card, CaseOutcome, ItemStatus, Selector, Template, TemplateCase

NOW = datetime(2026, 11, 14, tzinfo=UTC)

FORM = """class Box:
    def __init__(self, value):
        self.value = value


def build(xs):
    return [Box(x) for x in xs]


def solve(xs):
    boxes = build(xs)
    best = boxes[0].value  # the first is the best so far
    for box in boxes:
        if box.value > best:
            best = box.value
    return best
"""

CASES = [
    TemplateCase(args=[[3, 9, 4]], expected=9),
    TemplateCase(args=[[7]], expected=7),
    TemplateCase(args=[[2, 5, 5, 1]], expected=5),
]


def template(code: str = FORM, **overrides) -> Template:
    return Template.model_validate(
        {
            "id": "t-1",
            "slug": "largest",
            "title": "largest",
            "trigger": "the largest value",
            "code": code,
            "cases": CASES,
            "harness": ["Box", "build"],
        }
        | overrides
    )


def card(*templates: Template) -> Card:
    return Card(
        id="c-1",
        slug="largest-card",
        technique="sorting",
        title="largest",
        trigger="a choice",
        brief="## Core idea",
        templates=list(templates) or [template()],
        selector=Selector(technique="sorting", size=3),
    )


def test_an_item_shows_neither_the_comments_nor_the_harness():
    view = shown(FORM, ["Box", "build"])

    assert "#" not in view
    assert "class Box" not in view and "def build" not in view
    assert view.startswith("def solve(xs):")


def test_a_template_yields_one_clean_item_and_flaws_on_different_lines():
    built = items(template(), now=NOW)

    assert [one.clean for one in built][0] is True
    flawed = [one for one in built if not one.clean]
    assert 1 <= len(flawed) <= 3
    assert len({one.line for one in flawed}) == len(flawed)


def test_a_flawed_item_carries_the_case_its_code_fails():
    for one in items(template(), now=NOW):
        if one.clean:
            continue
        assert one.outcome in (CaseOutcome.WRONG, CaseOutcome.CRASHED)
        assert one.case_args is not None
        assert one.returned != one.case_expected


def test_no_item_line_is_wider_than_the_column():
    for one in items(template(), now=NOW):
        assert max(len(line) for line in one.code.splitlines()) <= WIDTH


def test_a_form_wider_than_the_column_yields_no_item():
    wide = FORM.replace("best = box.value", "best = box.value" + " + 0" * 15)

    assert items(template(code=wide), now=NOW) == []


def test_a_flawed_line_is_a_line_of_the_form_shown():
    """The harness is hidden, so a flaw there could be neither read nor
    tapped."""
    for one in items(template(), now=NOW):
        if not one.clean:
            assert one.line is not None
            assert one.code.splitlines()[one.line - 1].strip()


def test_a_build_leaves_a_template_served_at_its_code_alone():
    first, _ = build([card()], [], now=NOW)

    again, retired = build([card()], first, now=NOW)

    assert (again, retired) == ([], [])


def test_a_template_whose_code_moved_retires_its_items():
    first, _ = build([card()], [], now=NOW)
    moved = template(code=FORM.replace("boxes[0]", "boxes[-1]"))

    added, retired = build([card(moved)], first, now=NOW)

    assert sorted(retired) == sorted(one.id for one in first)
    assert added and all(one.form_digest == digest(moved.code) for one in added)


def test_items_are_stored_and_retired_by_status(database):
    (held,) = seeded(
        database,
        card_record(
            templates=[
                template_record(
                    "largest",
                    code=FORM,
                    cases=[c.model_dump() for c in CASES],
                    harness=["Box", "build"],
                )
            ]
        ),
    )
    store = ItemStore(database)
    added, _ = build([held], [], now=NOW)
    store.add(added)

    store.retire([added[0].id])

    assert {one.id: one.status for one in store.all()}[added[0].id] is ItemStatus.RETIRED
    assert len(store.served()) == len(added) - 1


def test_a_flawed_item_keeps_the_author_s_formatting():
    """Mutants are rebuilt from the tree, which reformats the whole file. The
    item splices the one change into the author's own code instead."""
    code = (
        "def solve(xs):\n"
        "    best = xs[0]\n"
        "    for x in xs:\n"
        "        if x > best:\n"
        "            best = x\n"
        '    return best  # the "largest"\n'
    )
    one = template(code=code, harness=[])

    flawed = [item for item in items(one, now=NOW) if not item.clean]

    assert flawed
    for item in flawed:
        changed = [
            line
            for line, base in zip(item.code.splitlines(), shown(code, []).splitlines(), strict=True)
            if line != base
        ]
        assert len(changed) == 1
