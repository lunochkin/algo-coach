from typing import Annotated

from fastapi import Depends, Request

from algo_coach.storage import Database


def _root(request: Request) -> Database:
    return request.app.state.root


def _user_id(request: Request) -> str:
    return request.app.state.user_id


Root = Annotated[Database, Depends(_root)]
UserId = Annotated[str, Depends(_user_id)]
