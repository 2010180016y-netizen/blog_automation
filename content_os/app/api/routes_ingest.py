from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from ..ingest.naver_commerce.client import NaverCommerceClient
from ..ingest.naver_commerce.sync import sync_my_store_products
from ..storage.repo import ProductRepo

router = APIRouter(prefix="/ingest", tags=["ingest"])
audit_logger = logging.getLogger("content_os.audit.ingest")


class IngestRequest(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    db_path: str = "blogs.db"
    page: int = 1
    size: int = 100


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit_per_minute: int) -> bool:
        now = time.time()
        cutoff = now - 60
        with self._lock:
            q = self._events[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= limit_per_minute:
                return False
            q.append(now)
            return True


_limiter = InMemoryRateLimiter()


def _require_ingest_auth(authorization: str | None, x_api_key: str | None) -> str:
    expected_api_key = os.getenv("INGEST_API_KEY")
    expected_bearer = os.getenv("INGEST_BEARER_TOKEN")

    if not expected_api_key and not expected_bearer:
        raise HTTPException(status_code=503, detail="ingest auth is not configured")

    if expected_api_key and x_api_key == expected_api_key:
        return "api_key"

    if expected_bearer and authorization:
        token = authorization[7:] if authorization.lower().startswith("bearer ") else ""
        if token and token == expected_bearer:
            return "bearer"

    raise HTTPException(status_code=401, detail="unauthorized")


def _check_ingest_rate_limit(client_key: str) -> None:
    limit = int(os.getenv("INGEST_RATE_LIMIT_PER_MINUTE", "30"))
    if limit <= 0:
        return
    if not _limiter.check(client_key, limit):
        raise HTTPException(status_code=429, detail="rate limit exceeded")


def _audit_ingest(request: Request, auth_type: str, status: str, detail: Dict) -> None:
    audit_logger.info(
        json.dumps(
            {
                "event": "ingest_my_store_sync",
                "path": str(request.url.path),
                "client": request.client.host if request.client else None,
                "auth_type": auth_type,
                "status": status,
                "detail": detail,
            },
            ensure_ascii=False,
        )
    )


@router.post("/my-store/sync")
def ingest_my_store(
    req: IngestRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    auth_type = _require_ingest_auth(authorization, x_api_key)
    client_key = f"{auth_type}:{request.client.host if request.client else 'unknown'}"
    _check_ingest_rate_limit(client_key)

    client = NaverCommerceClient(
        base_url=req.base_url,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )
    repo = ProductRepo(req.db_path)
    try:
        result = sync_my_store_products(client=client, repo=repo, page=req.page, size=req.size)
    except Exception as exc:
        _audit_ingest(request, auth_type=auth_type, status="ERROR", detail={"error": str(exc)})
        raise

    _audit_ingest(request, auth_type=auth_type, status="PASS", detail={"fetched": result.get("fetched", 0)})
    return result
