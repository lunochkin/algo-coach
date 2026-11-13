import json

from algo_coach.cards.check import check_card, siblings

FORM = "def solve(xs):\n    return sorted(xs)[0] if xs else None\n"


def template(**overrides) -> dict:
    return {
        "slug": "least",
        "title": "least",
        "trigger": "the smallest value",
        "code": FORM,
        "speedup": False,
        "cases": [{"args": [[3, 1, 2]], "expected": 1}, {"args": [[]], "expected": None}],
    } | overrides


def card(slug: str = "least-card", **overrides) -> dict:
    return {
        "slug": slug,
        "technique": "sorting",
        "title": slug,
        "trigger": "a choice",
        "brief": "## Core idea",
        "templates": [template()],
        "selector": {"technique": "sorting", "size": 3},
    } | overrides


def written(tmp_path, *cards: dict):
    for one in cards:
        (tmp_path / f"{one['slug']}.json").write_text(json.dumps(one))
    return tmp_path


def findings(tmp_path, slug: str = "least-card", **kwargs):
    path = tmp_path / f"{slug}.json"
    return [(one.check, one.message) for one in check_card(path, siblings(tmp_path), **kwargs)]


def test_a_sound_card_with_killing_cases_has_no_finding(tmp_path):
    written(
        tmp_path,
        card(
            templates=[
                template(
                    code="def solve(xs):\n    return min(xs)\n",
                    cases=[{"args": [[3, 1, 2]], "expected": 1}, {"args": [[5]], "expected": 5}],
                )
            ]
        ),
    )

    assert findings(tmp_path) == []


def test_a_file_the_schema_refuses_is_one_finding(tmp_path):
    (tmp_path / "least-card.json").write_text(json.dumps({"slug": "least-card"}))

    assert [check for check, _ in findings(tmp_path)] == ["schema"]


def test_an_unknown_technique_is_named(tmp_path):
    written(tmp_path, card(technique="nope"))

    assert ("technique", "unknown technique code: nope") in findings(tmp_path, mutate=False)


def test_a_file_named_apart_from_its_slug_is_named(tmp_path):
    (tmp_path / "other.json").write_text(json.dumps(card()))

    assert [check for check, _ in findings(tmp_path, "other", mutate=False)] == ["slug"]


def test_a_requirement_on_no_card_is_named(tmp_path):
    needs = [{"card": "gone", "template": "x", "used_by": "least"}]
    written(tmp_path, card(requires=needs))

    assert ("graph", "requires an unknown card: gone") in findings(tmp_path, mutate=False)


def test_a_case_the_form_fails_is_named(tmp_path):
    wrong = [{"args": [[3, 1, 2]], "expected": 3}]
    written(tmp_path, card(templates=[template(cases=wrong)]))

    assert [check for check, _ in findings(tmp_path)] == ["case"]


def test_a_set_answer_is_compared_in_any_order(tmp_path):
    form = "def solve(xs):\n    return list(reversed(xs))\n"
    cases = [{"args": [[1, 2]], "expected": [1, 2]}]
    written(tmp_path, card(templates=[template(code=form, cases=cases, unordered=True)]))

    assert "case" not in [check for check, _ in findings(tmp_path, mutate=False)]


def test_a_mutant_no_case_kills_is_named_with_its_line(tmp_path):
    """One ascending case never takes the branch, so flipping its comparison
    survives: a case the template lacks."""
    form = (
        "def solve(xs):\n"
        "    best = xs[0]\n"
        "    for x in xs:\n"
        "        if x < best:\n"
        "            best = x\n"
        "    return best\n"
    )
    cases = [{"args": [[1, 2, 3]], "expected": 1}]
    written(tmp_path, card(templates=[template(code=form, cases=cases)]))

    survivors = [message for check, message in findings(tmp_path) if check == "mutant"]
    assert any(message.startswith("line 4: < → <=") for message in survivors)


def test_a_survivor_accepted_as_equivalent_is_not_named(tmp_path):
    """`+ 0` shifted to `+ 1` is a real survivor here, and the test accepts it
    to check that an acceptance silences exactly that one."""
    form = "def solve(xs):\n    return max(xs) + 0\n"
    cases = [{"args": [[4, 9]], "expected": 9}]
    written(tmp_path, card(templates=[template(code=form, cases=cases)]))
    before = [message for check, message in findings(tmp_path) if check == "mutant"]
    accepted = before[0].removesuffix(" survives every case")

    written(tmp_path, card(templates=[template(code=form, cases=cases, equivalent=[accepted])]))

    after = [message for check, message in findings(tmp_path) if check == "mutant"]
    assert after == before[1:]


def test_an_acceptance_no_survivor_matches_is_stale(tmp_path):
    accepted = ["line 9: 0 → 1"]
    written(tmp_path, card(templates=[template(equivalent=accepted)]))

    stale = "line 9: 0 → 1 is accepted as equivalent, and no mutant survives as it"
    assert ("stale", stale) in findings(tmp_path)


def test_two_mutants_making_one_change_on_one_line_are_named_apart(tmp_path):
    """`1 + 1` holds two constants: shifting either one makes the same change,
    and an acceptance must name the one it means. Unused, so both survive."""
    form = "def solve(xs):\n    unused = 1 + 1\n    return len(xs)\n"
    cases = [{"args": [[]], "expected": 0}]
    written(tmp_path, card(templates=[template(code=form, cases=cases)]))

    named = [message for check, message in findings(tmp_path) if check == "mutant"]
    assert len(named) == len(set(named))
    assert any("(2nd)" in message for message in named)


def test_a_harness_naming_no_definition_is_named(tmp_path):
    written(tmp_path, card(templates=[template(harness=["TreeNode"])]))

    assert [check for check, _ in findings(tmp_path, mutate=False)] == ["harness"]
