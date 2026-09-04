import ast

from algo_coach.mutation import Operator, mutants

BINARY = """
def solve(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
"""


def changes(code: str, operator: Operator) -> list[str]:
    return [one.change for one in mutants(code) if one.operator is operator]


def codes(code: str) -> list[str]:
    return [one.code for one in mutants(code)]


def test_a_mutant_carries_one_change():
    """Two changes in one mutant would leave a survivor naming no single
    mistake."""
    code = "def solve(x):\n    return x < 1\n"

    for mutant in mutants(code):
        assert ast.unparse(ast.parse(mutant.code)) != ast.unparse(ast.parse(code))
        assert sum(a != b for a, b in zip(mutant.code.split(), code.split(), strict=False)) <= 1


def test_every_mutant_parses():
    """A mutant that does not parse is killed by the runner for the wrong
    reason."""
    for mutant in mutants(BINARY):
        ast.parse(mutant.code)


def test_a_comparison_yields_a_boundary_and_a_negation():
    """Off by one and the wrong direction are different mistakes, and a case
    set can catch one without the other."""
    code = "def solve(x):\n    return x < 2\n"

    assert changes(code, Operator.BOUNDARY) == ["< → <="]
    assert changes(code, Operator.NEGATION) == ["< → >="]


def test_equality_yields_a_negation_alone():
    """`==` has no neighbouring boundary to shift to."""
    code = "def solve(x):\n    return x == 2\n"

    assert changes(code, Operator.BOUNDARY) == []
    assert changes(code, Operator.NEGATION) == ["== → !="]


def test_each_operator_of_a_chained_comparison_is_its_own_site():
    """`0 <= i < n` holds two decisions, and one case can separate them."""
    code = "def solve(i, n):\n    return 0 <= i < n\n"

    assert changes(code, Operator.BOUNDARY) == ["<= → <", "< → <="]


def test_arithmetic_swaps_on_a_binary_operator_and_on_an_augmented_assign():
    code = "def solve(x):\n    total = x + 1\n    total *= 2\n    return total\n"

    assert changes(code, Operator.ARITHMETIC) == ["+ → -", "* → //"]


def test_a_connector_is_swapped():
    code = "def solve(a, b):\n    return a and b\n"

    assert changes(code, Operator.CONNECTOR) == ["and → or"]


def test_a_negated_condition_drops_its_not():
    code = "def solve(xs):\n    if not xs:\n        return 0\n    return len(xs)\n"

    assert changes(code, Operator.CONDITION) == ["not dropped"]
    assert "if xs:" in codes(code)[0]


def test_an_integer_constant_shifts_both_ways():
    """The off-by-one a case set most often misses."""
    code = "def solve(x):\n    return x + 3\n"

    assert changes(code, Operator.CONSTANT) == ["3 → 4", "3 → 2"]


def test_a_boolean_or_a_string_constant_is_not_shifted():
    """`True + 1` is 2, which is no mistake a solver makes."""
    code = 'def solve(x):\n    """Doubles."""\n    return x * 2 if True else "no"\n'

    assert changes(code, Operator.CONSTANT) == ["2 → 3", "2 → 1"]


def test_an_extremum_is_swapped():
    """Which end a greedy step takes is the mistake, and both calls
    type-check."""
    code = "def solve(a, b):\n    return min(a, b)\n"

    assert changes(code, Operator.EXTREMUM) == ["min → max"]


def test_a_jump_is_swapped():
    code = "def solve(xs):\n    for x in xs:\n        if x:\n            break\n    return x\n"

    assert changes(code, Operator.CONTROL) == ["break → continue"]


def test_a_comparison_inside_a_string_is_untouched():
    """The reason the change is made on the parsed tree rather than the
    text."""
    code = 'def solve(x):\n    return "a < b"\n'

    assert mutants(code) == []


def test_a_mutant_names_the_line_it_changed():
    """A survivor is reported at the decision it broke."""
    code = "def solve(x):\n    if x < len(x):\n        return x\n    return None\n"

    assert {one.line for one in mutants(code)} == {2}


def test_the_set_re_derives_the_same_way():
    """Nothing is stored, so a later run has to enumerate what an earlier one
    did."""
    assert mutants(BINARY) == mutants(BINARY)


def test_a_solution_with_no_site_yields_none():
    code = "def solve(xs):\n    return sorted(xs)\n"

    assert mutants(code) == []
