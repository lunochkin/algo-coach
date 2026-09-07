from algo_coach.generation import blind, generator, inputs, naive
from algo_coach.generation.contract import ALONE, ENTRY, RUNTIME, SIGNATURE

PROMPTS = (generator.SYSTEM, blind.SYSTEM, inputs.SYSTEM, naive.SYSTEM)


def test_every_brief_names_the_interpreter_it_runs_under():
    """A model writing for an older one reaches stdlib behaviour this rejects,
    and the crash costs the call that wrote the code."""
    assert RUNTIME.startswith("Python 3.")
    for prompt in PROMPTS:
        assert RUNTIME in prompt


def test_every_brief_asks_for_the_one_entry_point():
    """`corpus.md` gives it as an invariant: a stored name lets a statement and
    a solution disagree about what the runner calls."""
    for prompt in PROMPTS:
        assert ENTRY in prompt


def test_every_brief_says_the_code_stands_alone():
    """It is executed rather than read, so a module that prints or reads input
    answers no case."""
    for prompt in PROMPTS:
        assert ALONE in prompt


def test_every_brief_names_the_line_the_argument_order_is_read_from():
    """A reference took `solve(capacity, times, sizes)` where the canonical
    took `solve(times, sizes, capacity)`, so it answered no case and the
    problem was discarded."""
    for prompt in PROMPTS:
        assert "`def solve(...)` line" in prompt


def test_the_generator_is_told_to_end_the_statement_on_it():
    """It is the one prompt that writes the statement the other three read."""
    assert SIGNATURE in generator.SYSTEM
    assert "It ends with" in generator.SYSTEM


def test_the_input_generator_is_told_how_to_seed():
    """`random.seed` has taken integers alone since 3.11, and a tuple is what a
    model reaching for two numbers writes."""
    assert "Combine\nthem into one integer" in inputs.SYSTEM
