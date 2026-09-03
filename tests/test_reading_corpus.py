"""The classifier over the stored canonicals.

What a run adds to reading one solution is which ones to ask about: canonicals
only, and only where this configuration has not already answered the prompt it
would send now.
"""

import pytest
from helpers import CONFIGURATION, PROVENANCE, T0, FakeTransport, Verdict

from algo_coach.calls import CallLog, Configuration
from algo_coach.classifier import DEFAULT, request_hash
from algo_coach.mint import machine_reading, user_reading
from algo_coach.readings import Progress, ReadingLog, candidates, outstanding, read_corpus
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Solution, SolutionRole

answering = FakeTransport.answering

CODE = "def solve(xs):\n    return sorted(xs)[0]\n"


def solution(id: str, *, role: SolutionRole = SolutionRole.CANONICAL, code: str = CODE) -> Solution:
    return Solution(
        id=id,
        created_at=T0,
        problem_id=f"p-{id}",
        role=role,
        code=code,
        **PROVENANCE,
    )


def already_read(
    one: Solution,
    *,
    configuration: Configuration = CONFIGURATION,
    prompt_hash: str | None = None,
):
    """What this configuration would have written, had it read the solution."""
    return machine_reading(
        one.id,
        ["sorting"],
        model=configuration.model,
        effort=configuration.effort,
        prompt_hash=prompt_hash or request_hash(candidates(), one.code),
        call_id="call-0",
        pin=configuration.pin,
        temperature=configuration.temperature,
    )


@pytest.fixture
def log(tmp_path) -> ReadingLog:
    return ReadingLog(tmp_path)


def run(client, log, solutions, **kwargs):
    return read_corpus(
        client, log, CallLog(log.root), solutions, configuration=CONFIGURATION, **kwargs
    )


def test_every_canonical_is_read(log):
    client = answering(Verdict(["sorting"]), Verdict(["greedy"]))

    result = run(client, log, [solution("s1"), solution("s2")])

    assert result.read == 2
    assert {one.solution_id for one in log.readings()} == {"s1", "s2"}


def test_a_reference_is_never_read(log):
    """A problem's techniques are folded from its canonicals alone, so a
    reading of the reference would credit the approach the form replaces."""
    client = answering(Verdict(["sorting"]))

    result = run(client, log, [solution("s1", role=SolutionRole.REFERENCE), solution("s2")])

    assert result.read == 1
    assert [one.solution_id for one in log.readings()] == ["s2"]


def test_a_canonical_read_at_this_digest_is_skipped(log):
    """The reading answers the prompt this run would send, so paying for it
    again would buy the same verdict."""
    one = solution("s1")
    log.append(already_read(one))
    client = answering()

    result = run(client, log, [one])

    assert result.written == 0
    assert client.calls == []


def test_a_criteria_edit_re_reads_what_it_reached(log):
    """Staleness keys on the digest of what was sent, so a reading taken at
    another rulebook is answered again."""
    one = solution("s1")
    log.append(already_read(one, prompt_hash="an-older-rulebook"))
    client = answering(Verdict(["greedy"]))

    result = run(client, log, [one])

    assert result.read == 1
    assert [reading.techniques for reading in log.readings()] == [["sorting"], ["greedy"]]


def test_only_the_unread_canonicals_are_asked_about(log):
    """A run resumes where the last stopped: readings are appended as they are
    made, and the ones already at this digest drop out."""
    read, unread = solution("s1"), solution("s2", code="def solve(n):\n    return n\n")
    log.append(already_read(read))
    client = answering(Verdict(["greedy"]))

    result = run(client, log, [read, unread])

    assert result.read == 1
    assert unread.code in client.calls[0]["content"]
    assert [one.solution_id for one in log.readings()] == ["s1", "s2"]


def test_another_configuration_reads_again(log):
    """A reading is scored per configuration, so what one model answered is no
    answer from another."""
    one = solution("s1")
    another = DEFAULT.model_copy(update={"model": "another-model"})
    log.append(already_read(one, configuration=another))
    client = answering(Verdict(["greedy"]))

    result = run(client, log, [one])

    assert result.read == 1


def test_a_hand_reading_does_not_take_a_canonical_out_of_the_run(log):
    """The user's reading is what a configuration is scored against, so a
    machine reading of the same solution is what the score needs to exist."""
    one = solution("s1")
    log.append(user_reading(one.id, ["sorting"]))
    client = answering(Verdict(["greedy"]))

    result = run(client, log, [one])

    assert result.read == 1


def test_fresh_asks_again(log):
    """Measuring a reader against itself needs the question put twice."""
    one = solution("s1")
    log.append(already_read(one))
    client = answering(Verdict(["greedy"]))

    result = run(client, log, [one], fresh=True)

    assert result.read == 1
    assert len(log.readings()) == 2


def test_a_limit_bounds_what_a_run_pays_for(log):
    client = answering(Verdict(["sorting"]))

    result = run(client, log, [solution("s1"), solution("s2")], limit=1)

    assert result.written == 1
    assert len(client.calls) == 1


def test_an_empty_verdict_is_stored_and_counted_apart(log):
    """Naming none of the vocabulary is this reader's answer about the code.
    Unstored it would be paid for again on every later run."""
    client = answering(Verdict([]))

    result = run(client, log, [solution("s1")])

    assert (result.read, result.undecided, result.written) == (0, 1, 1)
    assert [one.techniques for one in log.readings()] == [[]]


def test_a_failure_leaves_the_canonicals_behind_it_readable(log):
    client = answering(Verdict(error=RuntimeError("dropped")), Verdict(["sorting"]))

    result = run(client, log, [solution("s1"), solution("s2")])

    assert result.read == 1
    assert [one.solution_id for one in result.failed] == ["s1"]
    assert not result.aborted


def test_consecutive_failures_abort_the_run(log):
    """A rejected key hits every solution, so a broken configuration stops
    rather than spending the corpus on it."""
    client = answering(*[Verdict(error=RuntimeError("bad key"))] * (ABORT_AFTER + 1))
    corpus = [solution(f"s{index}") for index in range(ABORT_AFTER + 1)]

    result = run(client, log, corpus)

    assert result.aborted
    assert len(result.failed) == ABORT_AFTER
    assert len(client.calls) == ABORT_AFTER


def test_progress_is_reported_as_the_run_goes(log):
    """A call per canonical makes a corpus run minutes long."""
    seen: list[Progress] = []
    client = answering(Verdict(["sorting"]), Verdict(error=RuntimeError("dropped")))

    run(client, log, [solution("s1"), solution("s2")], on_progress=seen.append)

    assert [(one.index, one.total, one.solution_id) for one in seen] == [
        (1, 2, "s1"),
        (2, 2, "s2"),
    ]
    assert [one.techniques for one in seen] == [["sorting"], []]
    assert seen[0].problem_id == "p-s1"
    assert seen[1].reason is not None


def test_outstanding_reads_the_digest_it_is_given(log):
    """The staleness rule alone: a record at the hash asked about takes its
    solution out, and one at another hash does not."""
    one, two = solution("s1"), solution("s2")
    hashes = {"s1": "current", "s2": "current"}
    readings = [already_read(one, prompt_hash="current"), already_read(two, prompt_hash="older")]

    assert [
        left.id for left in outstanding([one, two], readings, hashes, configuration=CONFIGURATION)
    ] == ["s2"]
