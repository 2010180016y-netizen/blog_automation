from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

from ..publish.content_queue_state import ContentQueueService, QueueState

router = APIRouter(prefix="/queue", tags=["ContentQueue"])
service = ContentQueueService()


class QueueCreateRequest(BaseModel):
    sku: str
    intent: str
    source_type: str
    disclosure_required: bool = True
    payload: Optional[Dict] = None


class QueueTransitionRequest(BaseModel):
    next_state: QueueState
    note: Optional[str] = None


class QueueRefreshRequest(BaseModel):
    reason: str
    payload: Optional[Dict] = None


@router.post("")
async def create_queue_item(req: QueueCreateRequest):
    item_id = service.create_item(
        sku=req.sku,
        intent=req.intent,
        source_type=req.source_type,
        disclosure_required=req.disclosure_required,
        payload=req.payload,
    )
    return {"id": item_id, "status": "DRAFT"}


@router.post("/{item_id}/transition")
async def transition_queue_item(item_id: int, req: QueueTransitionRequest):
    try:
        res = service.transition(item_id=item_id, next_state=req.next_state, note=req.note)
        return {
            "id": res.item_id,
            "from_state": res.from_state,
            "to_state": res.to_state,
            "transitioned_at": res.transitioned_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{item_id}/refresh")
async def request_refresh(item_id: int, req: QueueRefreshRequest):
    try:
        refresh_id = service.request_refresh_for_published(item_id, req.reason, req.payload)
        return {"refresh_id": refresh_id, "status": "PENDING"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{item_id}")
async def get_item(item_id: int):
    try:
        row = service.get_item(item_id)
        return dict(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
