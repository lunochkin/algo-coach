from algo_coach.api.__main__ import app


def test_the_served_app_reads_its_user_from_the_environment(monkeypatch):
    """The user stands in for authentication, as the CLI's `--user` default
    does."""
    monkeypatch.setenv("ALGO_COACH_USER", "u-4f9c2a")

    assert app().state.user_id == "u-4f9c2a"
