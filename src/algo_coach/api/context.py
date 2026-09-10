from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request


def _root(request: Request) -> Path:
    return request.app.state.root


def _user_id(request: Request) -> str:
    return request.app.state.user_id


Root = Annotated[Path, Depends(_root)]
UserId = Annotated[str, Depends(_user_id)]
