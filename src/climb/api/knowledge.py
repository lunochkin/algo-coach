import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from climb.api.context import Root, UserId
from climb.knowledge import Synced, snapshot, sync

router = APIRouter(prefix="/knowledge")


@router.get("/snapshot")
def content(request: Request, root: Root, _user_id: UserId) -> Response:
    """Every live module, in the shape learn's app reads: `knowledge.md`. The
    app syncs often and the content moves only at a seed, so an unchanged
    snapshot answers 304."""
    body = json.dumps(snapshot(root), separators=(",", ":"), sort_keys=True)
    tag = f'"{hashlib.sha256(body.encode()).hexdigest()}"'
    if request.headers.get("if-none-match") == tag:
        return Response(status_code=304, headers={"etag": tag})
    return Response(body, media_type="application/json", headers={"etag": tag})


class Upload(BaseModel):
    device: str = Field(min_length=1)
    records: list[dict[str, Any]]
    # each table's last append order the client already holds
    since: dict[str, int] = {}


@router.post("/sync")
def synced(root: Root, user_id: UserId, upload: Upload) -> Synced:
    return sync(root, user_id, upload.device, upload.records, upload.since)
