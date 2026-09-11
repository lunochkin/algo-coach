from datetime import UTC, datetime

from sqlalchemy import select

from algo_coach.log import LIFETIME, Provider, hashed, opened, signed_in
from algo_coach.log.table import sessions


def stored(database) -> list:
    with database.connect() as conn:
        return list(conn.execute(select(sessions)))


def test_a_session_is_stored_under_its_token_s_hash(database):
    """The cookie carries the token, and a copy of the table would sign every
    user in if it carried the token too."""
    user_id = signed_in(database, Provider.GITHUB, "583231", "solver@example.com")

    token = opened(database, user_id)

    (session,) = stored(database)
    assert session.id == hashed(token) != token
    assert session.user_id == user_id
    assert session.revoked_at is None


def test_a_session_lasts_its_lifetime(database):
    user_id = signed_in(database, Provider.GITHUB, "583231", "solver@example.com")
    before = datetime.now(UTC)

    opened(database, user_id)

    (session,) = stored(database)
    assert session.expires_at - session.created_at == LIFETIME
    assert before <= session.created_at <= datetime.now(UTC)


def test_every_sign_in_opens_a_session_of_its_own(database):
    """A second browser signing in leaves the first one signed in."""
    user_id = signed_in(database, Provider.GITHUB, "583231", "solver@example.com")

    assert opened(database, user_id) != opened(database, user_id)
    assert len(stored(database)) == 2
