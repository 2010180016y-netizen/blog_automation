from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Dict
from ..track.event_collector import EventCollector

router = APIRouter(prefix="/track", tags=["Tracking"])
collector = EventCollector()

class EventRequest(BaseModel):
    event_type: str
    channel: str
    content_id: str
    sku: str
    intent: str
    metadata: Optional[Dict] = None

    @field_validator("event_type", "channel", "content_id", "sku", "intent")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

class RetentionPurgeRequest(BaseModel):
    retention_days: int = 90

@router.post("/event")
async def track_event(req: EventRequest):
    collector.collect(
        req.event_type, 
        req.channel, 
        req.content_id, 
        req.sku, 
        req.intent, 
        req.metadata
    )
    return {"status": "collected"}

@router.get("/summary")
async def get_summary():
    from ..track.metrics import MetricsAggregator
    agg = MetricsAggregator()
    return agg.get_summary_by_content()


@router.post("/purge")
async def purge_events(req: RetentionPurgeRequest):
    try:
        deleted = collector.purge_old_events(req.retention_days)
        return {"status": "purged", "deleted": deleted, "retention_days": req.retention_days}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
