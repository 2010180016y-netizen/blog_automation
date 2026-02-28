import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..publish.queue import PublishQueue, SQLiteQueueStorage
from ..publish.state_machine import ContentState

router = APIRouter(prefix="/publish", tags=["Publishing"])

QUEUE_CONFIG = {
    "publishing": {
        "governance": {
            "require_human_approval_for": ["naver"]
        }
    }
}

queue_db_path = os.getenv("PUBLISH_QUEUE_DB_PATH", "publish_queue.db")
queue = PublishQueue(QUEUE_CONFIG, storage=SQLiteQueueStorage(queue_db_path))


class StateUpdate(BaseModel):
    content_id: str
    next_state: ContentState


class EnqueueRequest(BaseModel):
    content_id: str
    data: Dict[str, Any]


@router.post("/enqueue")
async def enqueue_item(req: EnqueueRequest):
    queue.add_item(req.content_id, req.data)
    return {"status": "enqueued", "content_id": req.content_id}


@router.post("/transition")
async def transition_state(update: StateUpdate):
    try:
        queue.update_state(update.content_id, update.next_state)
        return {"status": "success", "new_state": update.next_state}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approve/{content_id}")
async def approve_item(content_id: str):
    queue.approve(content_id)
    return {"status": "approved"}


@router.get("/queue/{platform}")
async def get_queue(platform: str):
    return queue.get_ready_items(platform)
