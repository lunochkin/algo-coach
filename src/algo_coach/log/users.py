from sqlalchemy import Connection, func
from sqlalchemy.dialects.postgresql import insert

from algo_coach.log.table import users


def known(conn: Connection, user_id: str) -> None:
    # added on a private record's first write, until Phase 9 links accounts
    conn.execute(insert(users).values(id=user_id, created_at=func.now()).on_conflict_do_nothing())
