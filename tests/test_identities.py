import pytest
from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError

from algo_coach.log import Provider, signed_in
from algo_coach.log.table import identities, users

EMAIL = "solver@example.com"


def counted(database, table) -> int:
    with database.connect() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar_one()


def emails(database) -> list[str]:
    with database.connect() as conn:
        return list(conn.execute(select(identities.c.email)).scalars())


def test_the_first_sign_in_mints_a_user_and_links_the_account(database):
    user_id = signed_in(database, Provider.GITHUB, "583231", EMAIL)

    with database.connect() as conn:
        linked = conn.execute(select(identities.c.provider, identities.c.user_id)).one()
        minted = conn.execute(select(users.c.id)).scalar_one()
    assert tuple(linked) == (Provider.GITHUB, user_id)
    assert minted == user_id


def test_a_later_sign_in_reaches_the_same_user(database):
    """The log keys on the engine's id, so an account that minted a user on
    every sign-in would find its history gone."""
    first = signed_in(database, Provider.GOOGLE, "108234", EMAIL)

    assert signed_in(database, Provider.GOOGLE, "108234", EMAIL) == first
    assert counted(database, users) == 1


def test_a_second_provider_with_the_same_email_joins_the_same_user(database):
    """One person signs in with either account and reaches one log."""
    at_google = signed_in(database, Provider.GOOGLE, "108234", EMAIL)

    assert signed_in(database, Provider.GITHUB, "583231", EMAIL) == at_google
    assert counted(database, users) == 1
    assert counted(database, identities) == 2


def test_an_email_is_matched_whatever_its_case(database):
    at_google = signed_in(database, Provider.GOOGLE, "108234", EMAIL)

    assert signed_in(database, Provider.GITHUB, "583231", EMAIL.upper()) == at_google
    assert emails(database) == [EMAIL, EMAIL]


def test_accounts_with_other_emails_are_other_users(database):
    """A provider's id means something at that provider alone, so a GitHub
    account whose number matches a Google one joins nothing by it."""
    at_google = signed_in(database, Provider.GOOGLE, "42", EMAIL)

    assert signed_in(database, Provider.GITHUB, "42", "other@example.com") != at_google


def test_a_known_account_keeps_its_user_when_its_email_moves(database):
    """The provider's id is the account, and the stored email follows the one
    the latest sign-in gave, which is what a later account is matched by."""
    first = signed_in(database, Provider.GITHUB, "583231", EMAIL)

    assert signed_in(database, Provider.GITHUB, "583231", "moved@example.com") == first
    assert emails(database) == ["moved@example.com"]
    assert signed_in(database, Provider.GOOGLE, "108234", "moved@example.com") == first


def test_an_account_is_linked_once(database):
    """A first sign-in racing another of the same account fails here, and its
    user rolls back with it rather than standing unlinked."""
    signed_in(database, Provider.GITHUB, "583231", EMAIL)
    second = signed_in(database, Provider.GITHUB, "777", "other@example.com")

    with pytest.raises(IntegrityError), database.begin() as conn:
        conn.execute(
            insert(identities).values(
                provider=Provider.GITHUB,
                provider_user_id="583231",
                user_id=second,
                email="other@example.com",
                created_at=func.now(),
            )
        )


def test_an_identity_names_a_user_the_engine_minted(database):
    with pytest.raises(IntegrityError), database.begin() as conn:
        conn.execute(
            insert(identities).values(
                provider=Provider.GOOGLE,
                provider_user_id="108234",
                user_id="nobody",
                email=EMAIL,
                created_at=func.now(),
            )
        )
