from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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
