from algo_coach.runner import NoValue, RunOutcome, outputs

DOUBLE = "def solve(n):\n    return n * 2\n"


def test_a_case_reports_the_value_it_returned():
    assert outputs(DOUBLE, [[1], [2], [3]], cap_ms=3000) == [2, 4, 6]


def test_a_case_that_yielded_nothing_says_how():
    """A canonical that crashed discards the problem, where a reference that
    did so is the ordinary path beyond its reach. Only the outcome separates
    them from a case that answered."""
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    assert outputs(code, [[1], [2]], cap_ms=3000) == [1, NoValue(RunOutcome.CRASHED)]


def test_a_case_past_the_cap_yields_nothing_too():
    code = "def solve(n):\n    while n:\n        pass\n    return n\n"

    assert outputs(code, [[0], [1]], cap_ms=200) == [0, NoValue(RunOutcome.TIMEOUT)]


def test_a_solution_returning_an_outcome_is_not_read_as_one():
    """`RunOutcome` is a `StrEnum`, so a bare outcome would make a solution
    returning `"timeout"` indistinguishable from one that ran past the cap."""
    code = "def solve():\n    return 'timeout'\n"

    answered = outputs(code, [[]], cap_ms=3000)

    assert answered == ["timeout"]
    assert answered != [NoValue(RunOutcome.TIMEOUT)]


def test_a_solution_may_legitimately_return_nothing():
    """`None` is a value, and nothing about it says the case failed."""
    assert outputs("def solve():\n    return None\n", [[]], cap_ms=3000) == [None]


def test_every_case_of_a_solution_with_no_solve_yields_nothing():
    code = "def other():\n    return 1\n"

    assert outputs(code, [[1], [2]], cap_ms=3000) == [NoValue(RunOutcome.CRASHED)] * 2


def test_stop_early_shortens_the_answers_as_it_shortens_the_run():
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    assert outputs(code, [[1], [2], [3]], cap_ms=3000, stop_early=True) == [
        1,
        NoValue(RunOutcome.CRASHED),
    ]


def test_the_answers_line_up_with_the_cases():
    """`settle` pairs them positionally, and a run that answered a different
    number of cases decides nothing there."""
    assert len(outputs(DOUBLE, [[1], [2], [3], [4]], cap_ms=3000)) == 4
