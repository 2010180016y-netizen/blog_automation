from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from .client import NaverCommerceClient


def _safe_parse_json(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _build_enriched_row(client: NaverCommerceClient, product: Any) -> Dict[str, Any]:
    p = _safe_parse_json(product)
    channel_no = str(p.get("channelProductNo") or p.get("channel_product_no") or "")
    origin_no = str(p.get("originProductNo") or p.get("origin_product_no") or "")

    detail, origin = {}, {}
    if channel_no:
        try:
            detail = client.get_channel_product(channel_no)
        except Exception:
            detail = {}
    if origin_no:
        try:
            origin = client.get_origin_product(origin_no)
        except Exception:
            origin = {}

    name = detail.get("name") or detail.get("productName") or origin.get("name") or p.get("name")
    price = detail.get("salePrice") or detail.get("price") or origin.get("salePrice") or p.get("salePrice")
    shipping = detail.get("deliveryInfo", {}).get("baseFee") if isinstance(detail.get("deliveryInfo"), dict) else detail.get("shipping")
    link = detail.get("productUrl") or p.get("productUrl") or ""

    return {
        "sku": channel_no or origin_no,
        "channel_product_no": channel_no,
        "origin_product_no": origin_no,
        "name": name,
        "price": int(price) if isinstance(price, (int, float)) or (str(price).isdigit() if price is not None else False) else None,
        "shipping": str(shipping or ""),
        "product_link": link,
        "raw_search": json.dumps(p, ensure_ascii=False),
        "raw_channel": json.dumps(detail, ensure_ascii=False),
        "raw_origin": json.dumps(origin, ensure_ascii=False),
    }


def fetch_enriched_products(
    client: NaverCommerceClient,
    page: int = 1,
    size: int = 100,
    detail_workers: int | None = None,
) -> List[Dict[str, Any]]:
    data = client.search_products(page=page, size=size)
    items = data.get("contents") or data.get("products") or []
    if not isinstance(items, list):
        return []

    workers = detail_workers or int(os.getenv("NAVER_DETAIL_FETCH_WORKERS", "8"))
    workers = max(1, min(workers, len(items) or 1))

    if workers == 1:
        return [_build_enriched_row(client, item) for item in items]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda item: _build_enriched_row(client, item), items))
