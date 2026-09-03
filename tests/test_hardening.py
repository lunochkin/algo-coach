"""The mutation loop over a drafted problem: when it asks for a case, what it
does with the ones it is given, and where it stops."""

from dataclasses import dataclass, field

import pytest
from generating import proposed

from algo_coach.calls import CallLog, Reply
from algo_coach.generation import GenerationError, harden
from algo_coach.mutation import ROUNDS
from algo_coach.schema import ExpectedSource

# four mutation sites rather than eight: the same kill structure, at half
# the subprocesses a pass costs
CANONICAL = "def solve(n):\n    return n > 3\n"
BLIND = "def solve(n):\n    return not n <= 3\n"
CAP_MS = 2_000


@dataclass
class Answers:
    """One reply per round, in order. `None` is a call that answered nothing."""

    rounds: list[list | None] = field(default_factory=lambda: [None])
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        asked = self.rounds[min(len(self.calls) - 1, len(self.rounds) - 1)]
        if asked is None:
            return Reply(text=None, stop_reason="length")
        return Reply(text=proposed(*asked), stop_reason="stop")


@dataclass(frozen=True)
class Case:
    args: list
    expected: object


def run(tmp_path, model: Answers, cases: list[Case], *, canonical=CANONICAL, reference=BLIND):
    return harden(
        model,
        CallLog(tmp_path),
        "Return 1 above three.",
        canonical=canonical,
        reference=reference,
        cases=cases,
        cap_ms=CAP_MS,
    )


# every mutant of the canonical differs from it at one of these
WEAK = [Case(args=[0], expected=False), Case(args=[10], expected=True)]
# the boundary the weak set never reaches: `n > 4`, `n > 2` and `n >= 3`
BOUNDARY = [[4], [3]]


def test_a_canonical_with_no_mutant_asks_nothing(tmp_path):
    """Nothing was changed, so no case has to exist and no round is paid for."""
    model = Answers()

    hardened = run(tmp_path, model, WEAK, canonical="def solve(n):\n    return len([n])\n")

    assert model.calls == []
    assert hardened.mutants == 0
    assert hardened.rounds == 0


def test_a_set_that_kills_every_mutant_asks_no_call(tmp_path):
    """The bar is met by the cases the generation call already wrote."""
    model = Answers()
    kills = WEAK + [Case(args=[3], expected=False), Case(args=[4], expected=True)]

    hardened = run(tmp_path, model, kills)

    assert model.calls == []
    assert hardened.survived == 0
    assert hardened.cases == []


def test_a_survivor_draws_one_call_and_the_cases_it_wins_land(tmp_path):
    """A mutant no case kills names a case that has to exist, and the round is
    what writes it."""
    model = Answers(rounds=[BOUNDARY])

    hardened = run(tmp_path, model, WEAK)

    assert len(model.calls) == 1
    assert hardened.rounds == 1
    assert [one.args for one in hardened.cases] == BOUNDARY
    assert hardened.survived == 0


def test_a_won_case_carries_the_reference_s_answer(tmp_path):
    """Settled as the first set is: a case the canonical computed passes by
    construction."""
    hardened = run(tmp_path, Answers(rounds=[BOUNDARY]), WEAK)

    assert [one.expected for one in hardened.cases] == [True, False]
    assert {one.expected_from for one in hardened.cases} == {ExpectedSource.REFERENCE}


def test_a_won_case_names_the_round_that_proposed_it(tmp_path):
    """Not the call that wrote the problem: the round runs at its own
    configuration, and the stored case copies that one."""
    hardened = run(tmp_path, Answers(rounds=[BOUNDARY]), WEAK)

    assert {one.call.id for one in hardened.cases} == {hardened.call.id}


def test_the_cases_the_set_already_has_reach_the_call(tmp_path):
    """A proposal repeating one of them catches what that case already
    catches."""
    model = Answers(rounds=[BOUNDARY])

    run(tmp_path, model, WEAK)

    assert "[10]" in model.calls[0]["content"]


def test_a_proposal_the_canonical_cannot_answer_drops_the_case(tmp_path):
    """Nothing checks a proposed input against the constraints the statement
    gives, so a crash there says nothing about the solution."""
    model = Answers(rounds=[[["four"]]])

    hardened = run(tmp_path, model, WEAK)

    assert hardened.dropped == 1
    assert hardened.cases == []
    assert hardened.disagreement is None


def test_a_proposal_the_two_solutions_answer_differently_is_reported(tmp_path):
    """A boundary the first set never reached, read two ways. The caller
    discards the problem on it."""
    reference = "def solve(n):\n    return 99 if n == 4 else n > 3\n"
    model = Answers(rounds=[[[4]]])

    hardened = run(tmp_path, model, WEAK, reference=reference)

    assert hardened.disagreement is not None
    assert hardened.disagreement.canonical is True
    assert hardened.disagreement.reference == 99
    assert hardened.cases == []


def test_a_round_that_kills_nothing_stops_the_loop(tmp_path):
    """The next round asks the same question of the same survivors."""
    model = Answers(rounds=[[[5]]])

    hardened = run(tmp_path, model, WEAK)

    assert len(model.calls) == 1
    assert hardened.rounds == 1
    assert hardened.survived == 3


def test_the_loop_stops_at_the_bound(tmp_path):
    """A survivor two rounds did not kill is usually equivalent to the
    canonical, and no case kills an equivalent mutant."""
    model = Answers(rounds=[[[3]], [[5]]])

    hardened = run(tmp_path, model, WEAK)

    assert len(model.calls) == ROUNDS
    assert hardened.rounds == ROUNDS
    # `n > 4`, which only an input of 4 separates
    assert hardened.survived == 1


def test_a_call_that_answers_nothing_raises(tmp_path):
    """What a failed round costs is settled where the problem is, so the loop
    itself decides nothing about it."""
    with pytest.raises(GenerationError):
        run(tmp_path, Answers(), WEAK)
