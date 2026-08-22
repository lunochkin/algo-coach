"""The transport as the CLI builds it, and what it says while it waits.

A cap is absorbed by the transport on purpose — it is a fact about the
endpoint, not a reason to abandon a backlog. Absorbing it silently is what
made a held run read as a slow one.
"""

import argparse

import pytest

from algo_coach.calls import OpenRouter, Retry
from algo_coach.cli.transport import transport, warn


def retry(**overrides) -> Retry:
    fields = {
        "status": 429,
        "model": "openai/gpt-oss-120b",
        "pin": "deepinfra/bf16",
        "tries": 2,
        "of": 5,
        "pause": 15.0,
        "reason": "Rate limit exceeded",
    }
    return Retry(**{**fields, **overrides})


def test_a_wait_names_the_endpoint_it_is_held_by(capsys):
    """The endpoint rather than the model alone: a cap is per endpoint, and
    two configurations pinned to one are held by the same limit."""
    warn(retry())

    said = capsys.readouterr().err
    assert "429" in said
    assert "openai/gpt-oss-120b @ deepinfra/bf16" in said
    assert "try 2/5" in said
    assert "waiting 15s" in said


def test_a_wait_is_written_as_one_line(capsys):
    """Called on whichever thread made the request, while others print
    progress. Built in more than one write, the lines would interleave."""
    written: list[str] = []

    class Stream:
        def write(self, text: str) -> int:
            written.append(text)
            return len(text)

    import algo_coach.cli.transport as module

    original, module.sys.stderr = module.sys.stderr, Stream()
    try:
        warn(retry())
    finally:
        module.sys.stderr = original

    assert len(written) == 1
    assert written[0].endswith("\n")


def test_a_wait_the_status_is_unknown_for_still_reports(capsys):
    """A provider whose body carried no code is still a wait worth saying."""
    warn(retry(status=None))

    assert "failed" in capsys.readouterr().err


def test_the_transport_the_cli_builds_reports_its_waits(monkeypatch):
    """Wired once, where the transport is made. A command that forgot would be
    silent exactly where the run is slowest."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "a-key")
    args = argparse.Namespace(command="classify")

    built = transport(args, argparse.ArgumentParser())

    assert isinstance(built, OpenRouter)
    assert built.on_retry is warn


def test_no_key_is_the_configuration_being_wrong(monkeypatch):
    """Checked before the run: an unset key fails every attempt identically,
    and reporting that per attempt buries it."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    args = argparse.Namespace(command="classify")

    with pytest.raises(SystemExit) as exit_info:
        transport(args, argparse.ArgumentParser())

    assert exit_info.value.code == 2
