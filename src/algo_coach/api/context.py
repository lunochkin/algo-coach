from typing import Annotated

from fastapi import Depends, HTTPException, Request

from algo_coach.log import app_user_of, user_of
from algo_coach.storage import Database

# the cookie a signed-in browser carries its session's token in
SESSION_COOKIE = "session"


def _root(request: Request) -> Database:
    return request.app.state.root


Root = Annotated[Database, Depends(_root)]


def _user_id(request: Request, root: Root) -> str:
    # the session's user, read on every request: a revoked session ends at once
    token = request.cookies.get(SESSION_COOKIE)
    user_id = user_of(root, token) if token else None
    if user_id is None:
        raise HTTPException(401, "not signed in")
    return user_id


UserId = Annotated[str, Depends(_user_id)]


def _knowledge_user_id(request: Request, root: Root) -> str:
    # the app's bearer token, scoped to the knowledge endpoints alone, or the
    # pages' session: `README.md`
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        user_id = app_user_of(root, token)
        if user_id is None:
            raise HTTPException(401, "not signed in")
        return user_id
    return _user_id(request, root)


KnowledgeUserId = Annotated[str, Depends(_knowledge_user_id)]
