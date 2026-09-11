from sqlalchemy import Connection, func, select, update
from sqlalchemy.dialects.postgresql import insert

from algo_coach.ids import new_id
from algo_coach.log.table import Provider, identities, users
from algo_coach.storage import Database


def known(conn: Connection, user_id: str) -> None:
    # added on a private record's first write, until Phase 9 links accounts
    conn.execute(insert(users).values(id=user_id, created_at=func.now()).on_conflict_do_nothing())


def named(root: Database, user_id: str) -> None:
    """Adds the user a dev login signs in as, where nothing has named it yet."""
    with root.begin() as conn:
        known(conn, user_id)


def signed_in(root: Database, provider: Provider, provider_user_id: str, email: str) -> str:
    """The engine's user an account signs in as. `email` is one the provider
    verified: an unverified one would join whoever holds that address.

    A known account keeps its user. A new account joins the user of an account
    with the same email, and mints a user where none has it.
    """
    email = email.lower()
    account = (identities.c.provider == provider) & (
        identities.c.provider_user_id == provider_user_id
    )
    with root.begin() as conn:
        linked = conn.execute(select(identities.c.user_id).where(account)).scalar_one_or_none()
        if linked is not None:
            conn.execute(update(identities).where(account).values(email=email))
            return linked
        # the oldest, should an email have moved onto a second user's account
        user_id = conn.execute(
            select(identities.c.user_id)
            .where(identities.c.email == email)
            .order_by(identities.c.created_at)
            .limit(1)
        ).scalar_one_or_none()
        if user_id is None:
            user_id = new_id()
            # a first sign-in of the same account racing this one fails on the
            # primary key, and its user rolls back with it
            conn.execute(insert(users).values(id=user_id, created_at=func.now()))
        conn.execute(
            insert(identities).values(
                provider=provider,
                provider_user_id=provider_user_id,
                user_id=user_id,
                email=email,
                created_at=func.now(),
            )
        )
    return user_id
