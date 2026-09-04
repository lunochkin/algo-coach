from datetime import UTC, datetime

import pytest
from matching import card, seeded

from algo_coach.generation import Corpus, land
from algo_coach.schema import (
    Call,
    Draft,
    ExpectedSource,
    MachineProvenance,
    MatchSource,
    SettledCase,
    SolutionRole,
    WritingState,
)

CANONICAL = "def solve(xs):\n    return len(xs)\n"
BLIND = "def solve(xs):\n    return sum(1 for _ in xs)\n"


def call(id: str, **overrides) -> Call:
    return Call(
        id=id,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        model="a-model",
        effort="high",
        prompt="a brief",
        prompt_hash="0123456789ab",
        response="{}",
        pin="a-provider/bf16",
        provider="a-provider",
        **overrides,
    )


def written(one: Call) -> MachineProvenance:
    """The configuration a step copied off its call, as a draft holds it."""
    return MachineProvenance(
        model=one.model,
        effort=one.effort,
        prompt_hash=one.prompt_hash,
        call_id=one.id,
        pin=one.pin or "",
        temperature=one.temperature,
        provider=one.provider,
    )


def drafted(**overrides) -> Draft:
    fields = {
        "cases": [
            SettledCase(
                args=[[1, 2, 3]],
                expected=3,
                expected_from=ExpectedSource.REFERENCE,
                written=MachineProvenance.of(call("call-3")),
            )
        ]
    } | overrides
    return Draft(
        id="w1",
        state=WritingState.HARDENED,
        title="Widest fair stretch",
        statement="Given a list of readings, return ...",
        canonical=CANONICAL,
        declared=[{"args": [[1, 2, 3]], "expected": 3}],
        difficulty="medium",
        reference=BLIND,
        generator=written(call("call-1")),
        blind=written(call("call-2", temperature=0.0)),
        **fields,
    )


@pytest.fixture
def template(tmp_path):
    """A seeded card's template, since a match references a minted id and a
    seed file carries none."""
    (one,) = seeded(tmp_path, card())
    return one.templates[0]


def test_one_act_writes_every_part(tmp_path, template):
    """A statement with no cases is one nothing can judge, and the matcher
    reads whatever the problem store holds."""
    corpus = Corpus.at(tmp_path)

    problem = land(corpus, template, drafted())

    assert corpus.problems.all() == [problem]
    assert [one.expected for one in corpus.cases.for_problem(problem.id)] == [3]
    assert [one.role for one in corpus.solutions.for_problem(problem.id)] == [
        SolutionRole.CANONICAL,
        SolutionRole.REFERENCE,
    ]
    assert [(one.template_id, one.source, one.matched) for one in corpus.matches.matches()] == [
        (template.id, MatchSource.GENERATOR, True)
    ]


NAIVE = "def solve(xs):\n    return len([one for one in xs])\n"


def test_the_clock_lands_beside_the_two_other_solutions(tmp_path, template):
    """A replay re-runs the search over the stored problem, and re-deriving the
    solution it measures against would re-pay the call that wrote it."""
    corpus = Corpus.at(tmp_path)

    problem = land(
        corpus, template, drafted(naive=NAIVE, clock=written(call("call-4", temperature=None)))
    )

    stored = corpus.solutions.for_problem(problem.id, SolutionRole.NAIVE)
    assert [one.code for one in stored] == [NAIVE]
    # its own call rather than the problem's: a configuration is per call site
    assert [one.call_id for one in stored] == ["call-4"]


def test_a_form_that_is_its_own_optimum_lands_no_clock(tmp_path, template):
    """Nothing measures it, so the draft carries none and the corpus stores
    none."""
    corpus = Corpus.at(tmp_path)

    problem = land(corpus, template, drafted())

    assert corpus.solutions.for_problem(problem.id, SolutionRole.NAIVE) == []


def test_the_problem_is_written_last(tmp_path, template, monkeypatch):
    """Four stores cannot be written atomically. A run that dies part way
    leaves records pointing at a problem no reader finds, rather than a problem
    whose parts are missing."""
    corpus = Corpus.at(tmp_path)
    monkeypatch.setattr(
        corpus.problems, "put", lambda _problem: (_ for _ in ()).throw(OSError("disk"))
    )

    with pytest.raises(OSError):
        land(corpus, template, drafted())

    assert corpus.problems.all() == []
    assert len(corpus.cases.cases()) == 1


def test_the_problem_carries_what_the_generation_call_asserted(tmp_path, template):
    """The template it was written for, its difficulty, and the configuration
    that wrote it."""
    problem = land(Corpus.at(tmp_path), template, drafted())

    assert problem.generated_for == template.id
    assert (problem.model, problem.effort, problem.call_id) == ("a-model", "high", "call-1")
    assert problem.difficulty == "medium"
    # a view over the problem's canonicals, derived rather than written here
    assert problem.techniques == []


def test_each_solution_names_the_call_that_wrote_it(tmp_path, template):
    """The canonical came from the generation call and the reference from its
    own, and a record whose configuration is partly unknown compares with
    nothing."""
    corpus = Corpus.at(tmp_path)

    problem = land(corpus, template, drafted())

    canonical, reference = corpus.solutions.for_problem(problem.id)
    assert (canonical.code, canonical.call_id) == (CANONICAL, "call-1")
    assert (reference.code, reference.call_id) == (BLIND, "call-2")
    assert (canonical.temperature, reference.temperature) == (None, 0.0)


def test_a_case_keeps_the_solution_that_computed_it(tmp_path, template):
    """Two cases in a set are not equally strong evidence, and the field is
    what says which is which."""
    beyond = drafted(
        cases=[
            SettledCase(
                args=[[1]],
                expected=1,
                expected_from=ExpectedSource.CANONICAL,
                written=MachineProvenance.of(call("call-3")),
            )
        ]
    )

    problem = land(Corpus.at(tmp_path), template, beyond)

    (one,) = Corpus.at(tmp_path).cases.for_problem(problem.id)
    assert one.expected_from is ExpectedSource.CANONICAL


def test_a_case_keeps_the_round_that_won_it(tmp_path, template):
    """A replay rebuilds the set the mutation loop was run against, and only
    this separates a won case from the set written with the statement."""
    won = drafted(
        cases=[
            SettledCase(
                args=[[1]],
                expected=1,
                expected_from=ExpectedSource.REFERENCE,
                written=MachineProvenance.of(call("call-3")),
                round=2,
            )
        ]
    )

    problem = land(Corpus.at(tmp_path), template, won)

    (one,) = Corpus.at(tmp_path).cases.for_problem(problem.id)
    assert one.round == 2


def test_a_case_names_the_call_that_proposed_it(tmp_path, template):
    """A mutation round and the speedup search propose arguments at their own
    configuration, so the problem's call does not answer for every case."""
    problem = land(Corpus.at(tmp_path), template, drafted())

    (one,) = Corpus.at(tmp_path).cases.for_problem(problem.id)
    assert one.call_id == "call-3"
