from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..storage.repo import ProductRepo

router = APIRouter(prefix="/ops", tags=["ops"])


class PlanningUpdateRequest(BaseModel):
    sku: str
    excluded: bool | None = None
    priority: int | None = None
    preferred_template: str | None = None
    preferred_intent: str | None = None
    notes: str | None = None
    db_path: str = "blogs.db"


@router.get("/products")
def list_products(db_path: str = "blogs.db", include_excluded: bool = True):
    repo = ProductRepo(db_path)
    return repo.list_products(include_excluded=include_excluded)


@router.post("/products/planning")
def update_product_planning(req: PlanningUpdateRequest):
    repo = ProductRepo(req.db_path)
    repo.set_product_planning(
        sku=req.sku,
        excluded=req.excluded,
        priority=req.priority,
        preferred_template=req.preferred_template,
        preferred_intent=req.preferred_intent,
        notes=req.notes,
    )
    return {"status": "ok", "sku": req.sku}


@router.get("/content-candidates")
def content_candidates(db_path: str = "blogs.db", limit: int = 50):
    repo = ProductRepo(db_path)
    return repo.build_content_candidates(limit=limit)


@router.get("/dashboard", response_class=HTMLResponse)
def ops_dashboard() -> str:
    return """
    <html>
      <head><title>Content OS Admin</title></head>
      <body>
        <h1>Content OS 상품 운영 대시보드</h1>
        <ul>
          <li>GET /ops/products?db_path=blogs.db</li>
          <li>POST /ops/products/planning</li>
          <li>GET /ops/content-candidates?db_path=blogs.db</li>
        </ul>
        <p>priority/excluded/template/intent를 조정해 수익화 글 큐를 운영하세요.</p>
      </body>
    </html>
    """.strip()
