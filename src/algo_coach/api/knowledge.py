from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from algo_coach.api.context import KnowledgeUserId, Root
from algo_coach.knowledge import Synced, snapshot, sync

router = APIRouter(prefix="/knowledge")


@router.get("/snapshot")
def content(root: Root, _user_id: KnowledgeUserId) -> dict[str, Any]:
    """Every live module, in the shape learn's app reads: `knowledge.md`."""
    return snapshot(root)


class Upload(BaseModel):
    device: str = Field(min_length=1)
    records: list[dict[str, Any]]
    # each table's last append order the client already holds
    since: dict[str, int] = {}


@router.post("/sync")
def synced(root: Root, user_id: KnowledgeUserId, upload: Upload) -> Synced:
    return sync(root, user_id, upload.device, upload.records, upload.since)
