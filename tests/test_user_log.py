import io
import json

import pytest
from commands import connected, run_cli
from helpers import PROVENANCE, PROVENANCE_FIELDS, T0, browsing, logged, machine_claim, seed_problem
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

from algo_coach import mint
from algo_coach.calls.table import calls
from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore, erased, whole_log
from algo_coach.log.table import attempts, sessions, users
from algo_coach.schema import Diagnosis, FailureMode

AUTHOR = "u-4f9c2a"
OTHER = "u-b71e03"
DOUBLE = "def solve(n):\n    return n * 2\n"


@pytest.fixture
def practised(database):
    """Both users' logs, each written as the drill loop writes one, with a
    machine claim and a diagnosis beside the loop's own records."""
    seed_problem(database, id="p1", techniques=["greedy", "sorting"])
    for args, expected in (([1], 2), ([3], 6)):
        CaseLog(database).append(mint.case("p1", args, expected, provenance=PROVENANCE))
    for user_id in (AUTHOR, OTHER):
        practise(database, user_id)
    return database


def practise(database, user_id: str) -> None:
    client = browsing(database, user_id)
    sitting_id = client.post("/api/problems/p1/sittings").json()["sitting"]["id"]
    client.post(f"/api/sittings/{sitting_id}/pause")
    client.post(f"/api/sittings/{sitting_id}/resume")
    submitted = client.post(f"/api/sittings/{sitting_id}/submissions", json={"code": DOUBLE})
    attempt_id = submitted.json()["attempt"]["id"]
    client.post(
        f"/api/attempts/{attempt_id}/claims", json={"techniques": ["greedy"], "confidence": "sure"}
    )
    log = AttemptLog(database)
    # a call about this user's code alone
    logged(log, machine_claim(attempt_id, ["sorting"], call_id=f"call-{user_id}"))
    log.append_self_label(mint.self_label(attempt_id, FailureMode.RUST))
    # naming the call the problem's cases name too, which erasing one log keeps
    log.append_diagnosis(
        Diagnosis(
            id=f"d-{user_id}",
            created_at=T0,
            attempt_id=attempt_id,
            mode=FailureMode.RUST,
            evidence="a timeout",
            **PROVENANCE_FIELDS,
        )
    )


def test_a_user_s_log_reads_out_whole_and_alone(practised):
    """Every record the loop, the classifier and the diagnoser wrote, and none
    of another user's."""
    read = whole_log(practised, AUTHOR)

    (sitting,) = read.sittings
    (attempt,) = read.attempts
    (verification,) = read.verifications
    assert sitting.user_id == attempt.user_id == AUTHOR
    assert len(sitting.pauses) == 1
    assert len(verification.results) == 2
    owned = {attempt.id}
    assert {one.attempt_id for one in [*read.claims, *read.self_labels, *read.diagnoses]} == owned
    assert len(read.claims) == 2
    assert {one.id for one in read.calls} == {f"call-{AUTHOR}", "call-1"}


def test_each_log_reader_reads_the_user_s_records_in_the_query(practised):
    """A reader given a user never loads another user's log to filter it."""
    log = AttemptLog(practised)

    assert {one.user_id for one in log.attempts(AUTHOR)} == {AUTHOR}
    assert {one.user_id for one in SittingStore(practised).all(OTHER)} == {OTHER}
    authored = {one.id for one in log.attempts(AUTHOR)}
    for records in (log.claims(AUTHOR), log.self_labels(AUTHOR), log.diagnoses(AUTHOR)):
        assert {one.attempt_id for one in records} == authored
    assert {one.attempt_id for one in log.verifications(AUTHOR)} == authored


def test_erasing_a_log_leaves_another_user_s_log_whole(practised):
    """The author's log is the evidence every eval reads, so another user's
    erasure must not reach it."""
    before = whole_log(practised, OTHER)

    erased(practised, AUTHOR)

    assert whole_log(practised, OTHER) == before
    emptied = whole_log(practised, AUTHOR)
    assert emptied.model_dump(exclude={"user_id"}) == {
        "sittings": [],
        "attempts": [],
        "verifications": [],
        "claims": [],
        "self_labels": [],
        "diagnoses": [],
        "calls": [],
    }


def test_erasing_counts_what_left_each_table(practised):
    counted = erased(practised, AUTHOR)

    assert counted == {
        "attempt_verification_case_results": 2,
        "attempt_verifications": 1,
        "attempt_claims": 2,
        "self_labels": 1,
        "diagnoses": 1,
        "attempts": 1,
        "sitting_pauses": 1,
        "sittings": 1,
        "calls": 1,
    }


def test_a_call_another_record_names_outlives_the_erasure(practised):
    """The problem's cases and the other user's diagnosis name the shared call,
    so only the call about the erased user's code goes."""
    erased(practised, AUTHOR)

    with practised.connect() as conn:
        left = set(conn.execute(select(calls.c.id)).scalars())
    assert f"call-{AUTHOR}" not in left
    assert {"call-1", f"call-{OTHER}"} <= left


def test_the_account_outlives_its_log(practised):
    """The log goes, and the user stays signed in to start a new one."""
    erased(practised, AUTHOR)

    with practised.connect() as conn:
        assert AUTHOR in set(conn.execute(select(users.c.id)).scalars())
        assert conn.execute(select(sessions.c.id).where(sessions.c.user_id == AUTHOR)).first()


def test_a_delete_outside_an_erasure_is_still_refused(practised):
    """The setting lasts the erasing transaction alone."""
    erased(practised, AUTHOR)

    with pytest.raises(ProgrammingError, match="append-only"), practised.begin() as conn:
        conn.execute(text("DELETE FROM attempts"))


def test_an_update_is_refused_even_while_erasing(practised):
    """Erasing deletes a whole log; no record is ever revised in place."""
    with pytest.raises(ProgrammingError, match="append-only"), practised.begin() as conn:
        conn.execute(text("SET LOCAL algo_coach.erasing = 'on'"))
        conn.execute(attempts.update().values(solved=False))


def test_the_terminal_prints_a_user_s_log(practised, monkeypatch, capsys):
    connected(practised, monkeypatch)

    run_cli(monkeypatch, "log", "export", "--user", AUTHOR)

    printed = json.loads(capsys.readouterr().out)
    assert printed["user_id"] == AUTHOR
    assert [one["user_id"] for one in printed["attempts"]] == [AUTHOR]


def test_the_terminal_erases_a_log_once_the_user_id_is_typed_back(practised, monkeypatch, capsys):
    connected(practised, monkeypatch)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{AUTHOR}\n"))

    run_cli(monkeypatch, "log", "erase", "--user", AUTHOR)

    assert "erased" in capsys.readouterr().out
    assert whole_log(practised, AUTHOR).attempts == []


def test_a_mistyped_confirmation_erases_nothing(practised, monkeypatch):
    connected(practised, monkeypatch)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{OTHER}\n"))

    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "log", "erase", "--user", AUTHOR)

    assert exit_info.value.code == 1
    assert len(whole_log(practised, AUTHOR).attempts) == 1


def test_erasing_names_its_user_every_time(monkeypatch):
    """A default would erase the author's own log."""
    monkeypatch.setenv("ALGO_COACH_DEV_LOGIN", AUTHOR)

    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "log", "erase")

    assert exit_info.value.code == 2
