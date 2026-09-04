import re
from datetime import timedelta
from importlib import import_module

import pytest
from helpers import T0, FakeTransport, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.calls import UNSENT
from algo_coach.classifier import EFFORT, MODEL, PIN, TEMPERATURE, request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim, user_claim
from algo_coach.schema import ClaimSource

TRANSPORT = import_module("algo_coach.cli.transport")


def run(monkeypatch, client: FakeTransport, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "score", "--user", "u1", *argv])
    cli.main()


def reading(attempt_id: str, techniques: list[str], *, model: str = MODEL):
    return classifier_claim(
        attempt_id,
        techniques,
        model=model,
        effort=EFFORT,
        prompt_hash=request_hash(["greedy", "sorting"], "def f(): pass"),
        call_id="call-1",
        pin=PIN,
        temperature=TEMPERATURE,
    )


@pytest.fixture
def hand_claimed(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    log = AttemptLog(data)
    log.append_attempt(attempt("a1", "two-codes"))
    log.append_claim(user_claim("a1", ["greedy"]))
    return log


def test_the_command_reports_the_agreement(hand_claimed, monkeypatch, capsys):
    run(monkeypatch, FakeTransport.answering(Verdict(["greedy"])))

    out = capsys.readouterr().out
    assert MODEL in out
    assert "1/1 exact (100%)" in out
    assert "greedy" in out


def test_the_rows_carry_what_was_over_claimed(hand_claimed, monkeypatch, capsys):
    run(monkeypatch, FakeTransport.answering(Verdict(["greedy", "sorting"])))

    out = capsys.readouterr().out
    assert "0/1 exact (0%)" in out
    assert "sorting" in out


def test_the_disagreements_are_printed_in_full(hand_claimed, monkeypatch, capsys):
    """Reading them is how a mislabelled hand claim is caught, and a corrected
    claim supersedes the earlier one."""
    run(monkeypatch, FakeTransport.answering(Verdict(["sorting"])))

    out = capsys.readouterr().out
    assert "a1" in out
    assert "you: greedy" in out
    assert "it:  sorting" in out


def test_the_command_says_what_it_paid_for(hand_claimed, monkeypatch, capsys):
    """A run is minutes of calls, and reuse is what the stored readings buy —
    so the cost is reported beside the share rather than inferred from it."""
    run(monkeypatch, FakeTransport.answering(Verdict(["greedy"])))
    capsys.readouterr()

    run(monkeypatch, FakeTransport.answering())

    out = capsys.readouterr().out
    assert re.search(r"read/reused\s+0/1", out)


def test_the_command_says_how_many_named_no_candidate(hand_claimed, monkeypatch, capsys):
    """A decline is scored like any other verdict, so it no longer buys a
    smaller denominator. It is still counted beside the share, since how often
    a classifier finds the candidates wanting is worth seeing on its own."""
    seed_problem(hand_claimed.root, id="second", techniques=["greedy", "sorting"])
    hand_claimed.append_attempt(attempt("a2", "second", finished_at=T0 + timedelta(days=1)))
    hand_claimed.append_claim(user_claim("a2", ["greedy"]))

    run(monkeypatch, FakeTransport.answering(Verdict([]), Verdict(["greedy"])))

    out = capsys.readouterr().out
    assert "1/2 exact (50%)" in out
    assert re.search(r"named no candidate\s+1", out)


def test_the_named_classifier_is_the_one_scored(hand_claimed, monkeypatch, capsys):
    run(
        monkeypatch,
        FakeTransport.answering(Verdict(["greedy"])),
        "--model",
        "a-cheap-model",
        "--provider",
        "a-host",
    )

    out = capsys.readouterr().out
    assert "a-cheap-model" in out
    assert "1/1 exact (100%)" in out


def test_the_effort_attaches_to_the_model_before_it(hand_claimed, monkeypatch, capsys):
    """Two configurations of one model, told apart by what each was asked at —
    which is lost the moment the flags are collected separately."""
    run(
        monkeypatch,
        FakeTransport.answering(Verdict(["greedy"]), Verdict(["sorting"])),
        *("--model", "a-model", "--provider", "a-host", "--effort", "low"),
        *("--model", "a-model", "--provider", "a-host", "--effort", "high"),
    )

    # A row each in the summary, which is where a configuration is spelled
    # out now that the table below it heads columns with a number.
    rows = [line for line in capsys.readouterr().out.splitlines() if "a-model" in line]
    assert [line.split()[0] for line in rows] == ["1", "2"]
    assert "low" in rows[0] and "high" in rows[1]


def test_the_same_configuration_twice_is_refused(hand_claimed, monkeypatch, capsys):
    """It would measure the classifier's own sampling noise — a real number,
    and one nothing here consumes yet."""
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeTransport.answering(),
            "--model",
            "a-model",
            "--provider",
            "a-host",
            "--model",
            "a-model",
            "--provider",
            "a-host",
        )

    assert exit_info.value.code == 2
    assert "named twice" in capsys.readouterr().err


def test_two_efforts_for_one_model_is_refused(hand_claimed, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering(), *("--effort", "low", "--effort", "high"))

    assert exit_info.value.code == 2
    assert "two --effort" in capsys.readouterr().err


def test_the_shares_are_over_what_both_read(hand_claimed, monkeypatch, capsys):
    """Two columns under one denominator: a cheaper classifier measured on its
    own smaller sample would read as the better one."""
    # Scripted per deployment: the two run at once, and which verdict each got
    # is exactly what these assertions are about.
    run(
        monkeypatch,
        FakeTransport.per_deployment(
            {
                (MODEL, PIN): Verdict(["greedy"]),
                ("a-cheap-model", "a-host"): Verdict(["sorting"]),
            }
        ),
        *("--model", MODEL, "--model", "a-cheap-model", "--provider", "a-host"),
        "--splits",
    )

    out = capsys.readouterr().out
    assert "1 hand-claimed attempts, 1 read by all" in out
    assert "1/1 (100%)" in out
    assert "0/1 (0%)" in out
    # The split names each configuration by its summary row, so the verdicts
    # line up with the numbers the technique table is headed by.
    assert re.search(r"1:\s+greedy", out)
    assert re.search(r"2:\s+sorting", out)
    # And the summary is where those numbers are spelled out.
    assert re.search(rf"1\s+{re.escape(MODEL)}\s+{EFFORT}\s+{TEMPERATURE}", out)
    assert re.search(rf"2\s+a-cheap-model\s+{EFFORT}\s+{TEMPERATURE}", out)


def test_a_classifier_that_fails_every_call_aborts(hand_claimed, monkeypatch, capsys):
    """A model that rejects a parameter fails identically on every attempt —
    the eval set must not be paid for to learn it once."""
    seed_problem(hand_claimed.root, id="second", techniques=["greedy", "sorting"])
    seed_problem(hand_claimed.root, id="third", techniques=["greedy", "sorting"])
    for index, name in enumerate(("second", "third"), start=2):
        hand_claimed.append_attempt(
            attempt(f"a{index}", name, finished_at=T0 + timedelta(days=index))
        )
        hand_claimed.append_claim(user_claim(f"a{index}", ["greedy"]))
    rejected = Verdict(error=RuntimeError("does not support the effort parameter"))

    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeTransport.answering(rejected, rejected, rejected),
            *("--model", "a-model", "--provider", "a-host"),
        )

    said = capsys.readouterr().err
    assert exit_info.value.code == 1
    assert "aborted after 3 consecutive failures" in said
    # Why, not only that. The numbers are withheld on this path, so nothing
    # else would ever say what the calls answered — and the board's tally
    # names no attempt.
    assert "does not support the effort parameter" in said
    assert "a1" in said


def test_an_unsupported_effort_can_be_left_unset(hand_claimed, monkeypatch, capsys):
    """`--effort default` is how a model that rejects the parameter is named:
    the level it ran at, stored like any other."""
    client = FakeTransport.answering(Verdict(["greedy"]))

    run(monkeypatch, client, *("--effort", "default"))

    (call,) = client.calls
    assert call["effort"] == UNSENT
    (reading,) = [c for c in hand_claimed.claims() if c.source is ClaimSource.CLASSIFIER]
    assert reading.effort == "default"


def test_a_stored_run_makes_no_call_and_needs_no_key(hand_claimed, monkeypatch, capsys):
    """What makes it the reproducible mode: it can be run anywhere, and
    twice."""
    hand_claimed.append_claim(reading("a1", ["greedy"]))
    for name in TRANSPORT.CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("sys.argv", ["algo-coach", "score", "--user", "u1", "--stored"])

    cli.main()

    assert "1/1 exact (100%)" in capsys.readouterr().out


def test_a_stored_run_with_a_limit_is_refused(hand_claimed, monkeypatch, capsys):
    """A cap on a run that pays for nothing states two different things."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering(), "--stored", "--limit", "5")

    assert exit_info.value.code == 2
    assert "--stored with --limit" in capsys.readouterr().err


def test_a_stored_run_over_nothing_read_exits_nonzero(hand_claimed, monkeypatch, capsys):
    """Ground truth exists and no reading of it does — told apart from having
    no ground truth at all, since only one of them is fixed by reading."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering(), "--stored")

    assert exit_info.value.code == 1
    assert "nothing every configuration named has read" in capsys.readouterr().err


def test_nothing_hand_claimed_exits_nonzero(tmp_path, monkeypatch, capsys):
    """No ground truth is not a score of zero — there is nothing to score."""
    data = tmp_path / "data"
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-codes"))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering())

    assert exit_info.value.code == 1
    assert "nothing hand-claimed" in capsys.readouterr().err


def test_a_provider_pins_the_model_before_it(hand_claimed, monkeypatch):
    """Flags into one ordered list, so which build belongs to which model
    survives the command line."""
    client = FakeTransport.answering(Verdict(["greedy"]), Verdict(["greedy"]))

    run(
        monkeypatch,
        client,
        *("--model", "a-model", "--provider", "a-host"),
        *("--model", "b-model", "--provider", "b-host"),
    )

    # Which pin stayed with which model, not which was asked first: the two
    # deployments run at once, so the order they reach the transport in is the
    # scheduler's rather than the command line's.
    assert {(call["model"], call["pin"]) for call in client.calls} == {
        ("a-model", "a-host"),
        ("b-model", "b-host"),
    }


def test_a_model_named_without_a_provider_is_refused(hand_claimed, monkeypatch, capsys):
    """Neither inherited nor left to the router. An endpoint carries some
    models and not others, so the built-in pin would route a model to a host
    that never serves it; and unpinned, the readings under one key would be a
    mixture of builds that no later run could take apart."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering(), "--model", "another/model")

    assert exit_info.value.code == 2
    assert "--provider needed for another/model" in capsys.readouterr().err


def test_the_temperature_attaches_to_the_model_before_it(hand_claimed, monkeypatch):
    """Fourth slot in the same ordered list, for the same reason as the other
    three: the command line's order is the output's, and separate destinations
    would lose which temperature followed which model."""
    client = FakeTransport.per_deployment(
        {
            ("a-model", "a-host"): Verdict(["greedy"]),
            ("b-model", "b-host"): Verdict(["sorting"]),
        }
    )

    run(
        monkeypatch,
        client,
        *("--model", "a-model", "--provider", "a-host", "--temperature", "0"),
        *("--model", "b-model", "--provider", "b-host", "--temperature", "1"),
    )

    assert {(call["model"], call["temperature"]) for call in client.calls} == {
        ("a-model", 0.0),
        ("b-model", 1.0),
    }


def test_two_temperatures_of_one_model_are_two_columns(hand_claimed, monkeypatch, capsys):
    """The comparison the field exists for. Same model and same effort, so a
    column named by those alone prints one heading twice and leaves the reader
    guessing which arm they are reading."""
    run(
        monkeypatch,
        FakeTransport.answering(Verdict(["greedy"]), Verdict(["sorting"])),
        *("--model", "a-model", "--provider", "a-host", "--temperature", "0"),
        *("--model", "a-model", "--provider", "a-host", "--temperature", "1"),
    )

    rows = [line for line in capsys.readouterr().out.splitlines() if "a-model" in line]
    assert len(rows) == 2
    # Same model and same effort, so only the temperature separates them.
    assert rows[0].split()[:4] == ["1", "a-model", EFFORT, "0.0"]
    assert rows[1].split()[:4] == ["2", "a-model", EFFORT, "1.0"]


def test_one_model_at_one_temperature_twice_is_still_refused(hand_claimed, monkeypatch, capsys):
    """Adding a field to the identity widens what counts as two configurations;
    it does not stop a repeat from being one."""
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeTransport.answering(),
            *("--model", "a-model", "--provider", "a-host", "--temperature", "0"),
            *("--model", "a-model", "--provider", "a-host", "--temperature", "0"),
        )

    assert exit_info.value.code == 2
    assert "named twice" in capsys.readouterr().err


def test_two_temperatures_for_one_model_is_refused(hand_claimed, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeTransport.answering(),
            *(
                "--model",
                "a-model",
                "--provider",
                "a-host",
                "--temperature",
                "0",
                "--temperature",
                "1",
            ),
        )

    assert exit_info.value.code == 2
    assert "two --temperature" in capsys.readouterr().err


def test_what_they_read_differently_is_counted_rather_than_printed(
    hand_claimed, monkeypatch, capsys
):
    """One split is a line per configuration, so ten configurations turn a
    handful of disagreements into hundreds of lines that mostly repeat."""
    run(
        monkeypatch,
        FakeTransport.per_deployment(
            {
                (MODEL, PIN): Verdict(["greedy"]),
                ("a-cheap-model", "a-host"): Verdict(["sorting"]),
            }
        ),
        *("--model", MODEL, "--model", "a-cheap-model", "--provider", "a-host"),
    )

    out = capsys.readouterr().out
    assert "1 read differently — --splits to see them" in out
    # The verdicts themselves are what the flag buys.
    assert not re.search(r"^\s+1:\s+greedy", out, re.MULTILINE)


def ranked(monkeypatch, *argv: str) -> None:
    """The worse classifier named first, so the command line's order and the
    ranking cannot agree by accident."""
    run(
        monkeypatch,
        FakeTransport.per_deployment(
            {
                ("a-cheap-model", "a-host"): Verdict(["sorting"]),
                (MODEL, PIN): Verdict(["greedy"]),
            }
        ),
        *("--model", "a-cheap-model", "--provider", "a-host", "--model", MODEL),
        *argv,
    )


def test_the_summary_is_ranked_by_the_exact_share(hand_claimed, monkeypatch, capsys):
    """What a comparison is read for is which classifier won. Finding that by
    eye down a column of twenty shares is work the sort does once."""
    ranked(monkeypatch)

    out = capsys.readouterr().out
    assert re.search(rf"1\s+{re.escape(MODEL)}\s+{EFFORT}\s+{TEMPERATURE}", out)
    assert re.search(rf"2\s+a-cheap-model\s+{EFFORT}\s+{TEMPERATURE}", out)


def test_a_split_follows_the_ranking_rather_than_the_command_line(
    hand_claimed, monkeypatch, capsys
):
    """A split's verdicts are positional, aligned with the scores. Reordering
    the summary alone would file each verdict under the wrong configuration."""
    ranked(monkeypatch, "--splits")

    out = capsys.readouterr().out
    assert re.search(r"1:\s+greedy", out)
    assert re.search(r"2:\s+sorting", out)


def test_the_per_technique_table_is_counted_rather_than_printed(hand_claimed, monkeypatch, capsys):
    """It grows a column per configuration, so a run comparing forty of them
    prints a table nothing can read across."""
    ranked(monkeypatch)

    out = capsys.readouterr().out
    assert "techniques — --splits to see them per configuration" in out
    assert "backtracking" not in out


def test_the_flag_prints_the_per_technique_table(hand_claimed, monkeypatch, capsys):
    ranked(monkeypatch, "--splits")

    out = capsys.readouterr().out
    assert re.search(r"technique\s+attempts\s+1\s+2", out)
    assert "greedy" in out


def test_one_configuration_reports_the_columns_the_comparison_does(
    hand_claimed, monkeypatch, capsys
):
    """One list of columns, laid down instead of across. Two renderers naming
    their own columns drift — this path said a decline was unscored long after
    declines started being scored."""
    # Reporting tokens, a price and a duration, so every optional column has
    # a number and the two renderers can be compared on all of them.
    one = FakeTransport.answering(Verdict(["greedy"]))
    one.tokens, one.request_ms, one.cost = (800, 40, 30), 1200, 0.0001
    run(monkeypatch, one)
    alone = capsys.readouterr().out

    two = FakeTransport.per_deployment(
        {
            (MODEL, PIN): Verdict(["greedy"]),
            ("a-cheap-model", "a-host"): Verdict(["greedy"]),
        }
    )
    two.tokens, two.request_ms, two.cost = (800, 40, 30), 1200, 0.0001
    run(monkeypatch, two, *("--model", MODEL, "--model", "a-cheap-model", "--provider", "a-host"))
    compared = capsys.readouterr().out

    for name in ("per decision", "read/reused", "in/out/think", "mean/max", "per attempt", "set"):
        assert name in alone, f"{name} missing from the single configuration"
        assert name in compared, f"{name} missing from the comparison"


def test_a_cut_short_reply_is_its_own_column(hand_claimed, monkeypatch, capsys):
    """A considered decline and a runaway decoder both name nothing, and only
    one of them is a reading. One column carrying both would have said they
    were a single number in two flavours."""
    seed_problem(hand_claimed.root, id="second", techniques=["greedy", "sorting"])
    hand_claimed.append_attempt(attempt("a2", "second", finished_at=T0 + timedelta(days=1)))
    hand_claimed.append_claim(user_claim("a2", ["greedy"]))

    run(
        monkeypatch,
        FakeTransport.answering(Verdict([]), Verdict(stop_reason="length", text="{  ")),
    )

    out = capsys.readouterr().out
    assert re.search(r"named no candidate\s+1", out)
    assert re.search(r"cut short\s+1", out)


def test_no_cut_short_column_where_nothing_was(hand_claimed, monkeypatch, capsys):
    """A column of zeroes is width spent saying nothing happened."""
    run(monkeypatch, FakeTransport.answering(Verdict([])))

    out = capsys.readouterr().out
    assert re.search(r"named no candidate\s+1", out)
    assert "cut short" not in out
