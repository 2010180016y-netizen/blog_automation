from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Dict

from ..track.event_collector import EventCollector
from ..track.link_builder import LinkBuilder

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


class BuildLinkRequest(BaseModel):
    base_url: str
    channel: str
    content_id: str
    sku: str
    intent: str
    metadata: Optional[Dict] = None

    @field_validator("base_url", "channel", "content_id", "sku", "intent")
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
        req.metadata,
    )
    return {"status": "collected"}


@router.post("/link")
async def build_tracking_link(req: BuildLinkRequest):
    builder = LinkBuilder(config={})
    tracking_url = builder.build_tracking_link(
        req.base_url,
        channel=req.channel,
        content_id=req.content_id,
        sku=req.sku,
        intent=req.intent,
    )
    collector.collect(
        event_type="link_built",
        channel=req.channel,
        content_id=req.content_id,
        sku=req.sku,
        intent=req.intent,
        metadata={
            "base_url": req.base_url,
            "tracking_url": tracking_url,
            **(req.metadata or {}),
        },
    )
    return {"status": "ok", "tracking_url": tracking_url}


@router.get("/summary")
async def get_summary():
    from ..track.metrics import MetricsAggregator

    agg = MetricsAggregator()
    return agg.get_summary_by_content()


@router.get("/kpi")
async def get_kpi():
    from ..track.metrics import MetricsAggregator

    agg = MetricsAggregator()
    return agg.get_kpi_report()


@router.post("/purge")
async def purge_events(req: RetentionPurgeRequest):
    try:
        deleted = collector.purge_old_events(req.retention_days)
        return {"status": "purged", "deleted": deleted, "retention_days": req.retention_days}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
