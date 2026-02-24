from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..publish.queue import PublishQueue
from ..publish.state_machine import ContentState

router = APIRouter(prefix="/publish", tags=["Publishing"])

# Shared queue instance (In-memory for MVP)
queue = PublishQueue({
    "publishing": {
        "governance": {
            "require_human_approval_for": ["naver"]
        }
    }
})

class StateUpdate(BaseModel):
    content_id: str
    next_state: ContentState

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
