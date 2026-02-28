from __future__ import annotations

from typing import Dict, List

from ...storage.repo import ProductRepo
from .client import NaverCommerceClient
from .products import fetch_enriched_products


def sync_my_store_products(client: NaverCommerceClient, repo: ProductRepo, page: int = 1, size: int = 100) -> Dict:
    rows = fetch_enriched_products(client, page=page, size=size)
    upsert_result = repo.upsert_products_ssot(rows)
    unified_result = repo.sync_unified_products_with_refresh()

    refresh_queue = unified_result.get("refresh_queue", {})
    enqueued = repo.enqueue_refresh_candidates(refresh_queue.get("skus", []), reason="MY_STORE_SYNC")

    return {
        "fetched": len(rows),
        "ssot": upsert_result,
        "refresh_queue": {**refresh_queue, **enqueued},
    }


def load_refresh_queue(db_path: str) -> List[str]:
    repo = ProductRepo(db_path)
    return repo.get_refresh_queue_skus()
