from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..ingest.naver_commerce.client import NaverCommerceClient
from ..ingest.naver_commerce.sync import sync_my_store_products
from ..storage.repo import ProductRepo

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    db_path: str = "blogs.db"
    page: int = 1
    size: int = 100


@router.post("/my-store/sync")
def ingest_my_store(req: IngestRequest):
    client = NaverCommerceClient(
        base_url=req.base_url,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )
    repo = ProductRepo(req.db_path)
    result = sync_my_store_products(client=client, repo=repo, page=req.page, size=req.size)
    return result
