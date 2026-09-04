from algo_coach.generation import blind, clock, generator, inputs
from algo_coach.generation.contract import ALONE, ENTRY, RUNTIME

BRIEFS = (generator.SYSTEM, blind.SYSTEM, inputs.SYSTEM, clock.SYSTEM)


def test_every_brief_names_the_interpreter_it_runs_under():
    """A model writing for an older one reaches stdlib behaviour this rejects,
    and the crash costs the call that wrote the code."""
    assert RUNTIME.startswith("Python 3.")
    for brief in BRIEFS:
        assert RUNTIME in brief


def test_every_brief_asks_for_the_one_entry_point():
    """`corpus.md` gives it as an invariant: a stored name lets a statement and
    a solution disagree about what the runner calls."""
    for brief in BRIEFS:
        assert ENTRY in brief


def test_every_brief_says_the_code_stands_alone():
    """It is executed rather than read, so a module that prints or reads input
    answers no case."""
    for brief in BRIEFS:
        assert ALONE in brief


def test_the_input_generator_is_told_how_to_seed():
    """`random.seed` has taken integers alone since 3.11, and a tuple is what a
    model reaching for two numbers writes."""
    assert "Combine\nthem into one integer" in inputs.SYSTEM
