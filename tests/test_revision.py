from datetime import timedelta

from helpers import T0, attempt, machine_claim, seed_problem

from algo_coach.claims import against, contested, revisable, standing_claims
from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.problems import load_problems


def pool(log):
    problems = {problem.id: problem for problem in load_problems(log.root)}
    return revisable(log.attempts(), problems, standing_claims(log.claims()), user_id="u1")


def test_only_what_the_hand_pass_answered_is_revisable(tmp_path):
    """`claimable`'s mirror: the same pool, the opposite filter."""
    root = tmp_path / "data"
    seed_problem(root, id="claimed", techniques=["greedy", "sorting"])
    seed_problem(root, id="unclaimed", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("a1", "claimed"))
    log.append_attempt(attempt("a2", "unclaimed"))
    log.append_claim(user_claim("a1", ["greedy"]))
    log.append_claim(machine_claim("a2", ["sorting"]))

    assert [a.id for a in pool(log)] == ["a1"]


def test_a_revision_asks_about_the_attempt_that_was_scored(tmp_path):
    """Collapsed before the filter, as the eval set is — asking about an older
    attempt would revise a claim no score ever read."""
    root = tmp_path / "data"
    seed_problem(root, id="p1", techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    log.append_attempt(attempt("older", "p1", finished_at=T0))
    log.append_attempt(attempt("latest", "p1", finished_at=T0 + timedelta(days=1)))
    log.append_claim(user_claim("older", ["greedy"]))
    log.append_claim(user_claim("latest", ["sorting"]))

    assert [a.id for a in pool(log)] == ["latest"]


def test_a_reading_naming_a_subset_disagrees(tmp_path):
    """Set equality, as the score uses: stopping at the first technique is a
    disagreement, not a partial answer."""
    claim = user_claim("a1", ["greedy", "sorting"])
    readings = [{"a1": machine_claim("a1", ["greedy"])}]

    assert against(claim, readings) == 1


def test_a_configuration_that_never_read_it_is_not_a_dissenter(tmp_path):
    """Silence is a third thing — counting it would report a disagreement
    nothing made."""
    claim = user_claim("a1", ["greedy"])
    readings = [{"a1": machine_claim("a1", ["greedy"])}, {}]

    assert against(claim, readings) == 0


def test_the_most_disputed_are_asked_about_first(tmp_path):
    """Every configuration disagreeing says the claim or the vocabulary is
    wrong; one disagreeing usually says that configuration is."""
    root = tmp_path / "data"
    for name in ("all", "one", "none"):
        seed_problem(root, id=name, techniques=["greedy", "sorting"])
    log = AttemptLog(root)
    for name in ("all", "one", "none"):
        log.append_attempt(attempt(name, name))
        log.append_claim(user_claim(name, ["greedy"]))
    standing = standing_claims(log.claims())
    readings = [
        {"all": machine_claim("all", ["sorting"]), "one": machine_claim("one", ["sorting"])},
        {"all": machine_claim("all", ["sorting"]), "one": machine_claim("one", ["greedy"])},
    ]

    ordered = contested(pool(log), standing, readings)

    assert [a.id for a in ordered] == ["all", "one"]
    assert [a.id for a in contested(pool(log), standing, readings, at_least=2)] == ["all"]
    assert len(contested(pool(log), standing, readings, at_least=0)) == 3
