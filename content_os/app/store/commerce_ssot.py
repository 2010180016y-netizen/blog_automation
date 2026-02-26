from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx


@dataclass
class CommerceAPIConfig:
    base_url: str
    token: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class NaverCommerceAPIClient:
    def __init__(self, config: CommerceAPIConfig, requester: Optional[Callable[..., httpx.Response]] = None):
        self.config = config
        self._requester = requester

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
        }
        if self.config.client_id:
            headers["X-Naver-Client-Id"] = self.config.client_id
        if self.config.client_secret:
            headers["X-Naver-Client-Secret"] = self.config.client_secret
        return headers

    def _request(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}{path}"
        if self._requester:
            response = self._requester(method=method, url=url, headers=self._headers(), json=json_body)
        else:
            with httpx.Client(timeout=20.0) as client:
                response = client.request(method=method, url=url, headers=self._headers(), json=json_body)
        response.raise_for_status()
        return response.json()

    def search_products(self, page: int = 1, size: int = 100) -> List[Dict[str, Any]]:
        payload = {"page": page, "size": size}
        data = self._request("POST", "/v1/products/search", json_body=payload)
        products = data.get("contents") or data.get("products") or []
        return products if isinstance(products, list) else []

    def get_channel_product(self, channel_product_no: str) -> Dict[str, Any]:
        return self._request("GET", f"/v2/products/channel-products/{channel_product_no}")

    def get_origin_product(self, origin_product_no: str) -> Dict[str, Any]:
        return self._request("GET", f"/v2/products/origin-products/{origin_product_no}")

    def fetch_ssot_rows(self, page: int = 1, size: int = 100) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for p in self.search_products(page=page, size=size):
            channel_no = str(p.get("channelProductNo") or p.get("channel_product_no") or "")
            origin_no = str(p.get("originProductNo") or p.get("origin_product_no") or "")

            detail = self.get_channel_product(channel_no) if channel_no else {}
            origin = self.get_origin_product(origin_no) if origin_no else {}

            name = (
                detail.get("name")
                or detail.get("productName")
                or origin.get("name")
                or p.get("name")
                or p.get("productName")
            )
            price = (
                detail.get("salePrice")
                or detail.get("price")
                or origin.get("salePrice")
                or p.get("salePrice")
                or p.get("price")
            )
            link = detail.get("productUrl") or p.get("productUrl") or ""
            shipping = (
                detail.get("deliveryInfo", {}).get("baseFee")
                if isinstance(detail.get("deliveryInfo"), dict)
                else detail.get("shipping")
            )

            rows.append(
                {
                    "sku": channel_no or origin_no,
                    "channel_product_no": channel_no,
                    "origin_product_no": origin_no,
                    "name": name,
                    "price": int(price) if price is not None and str(price).isdigit() else price,
                    "shipping": str(shipping) if shipping is not None else "",
                    "product_link": link,
                    "raw_search": json.dumps(p, ensure_ascii=False),
                    "raw_channel": json.dumps(detail, ensure_ascii=False),
                    "raw_origin": json.dumps(origin, ensure_ascii=False),
                }
            )
        return rows


def ensure_ssot_table(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products_ssot (
                sku TEXT PRIMARY KEY,
                channel_product_no TEXT,
                origin_product_no TEXT,
                name TEXT,
                price INTEGER,
                shipping TEXT,
                product_link TEXT,
                raw_search TEXT,
                raw_channel TEXT,
                raw_origin TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_ssot_rows(db_path: str, rows: List[Dict[str, Any]]) -> Dict[str, int]:
    ensure_ssot_table(db_path)
    inserted = 0
    with sqlite3.connect(db_path) as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO products_ssot(
                    sku, channel_product_no, origin_product_no, name, price, shipping, product_link,
                    raw_search, raw_channel, raw_origin, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(sku) DO UPDATE SET
                    channel_product_no=excluded.channel_product_no,
                    origin_product_no=excluded.origin_product_no,
                    name=excluded.name,
                    price=excluded.price,
                    shipping=excluded.shipping,
                    product_link=excluded.product_link,
                    raw_search=excluded.raw_search,
                    raw_channel=excluded.raw_channel,
                    raw_origin=excluded.raw_origin,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    row.get("sku"),
                    row.get("channel_product_no"),
                    row.get("origin_product_no"),
                    row.get("name"),
                    row.get("price"),
                    row.get("shipping"),
                    row.get("product_link"),
                    row.get("raw_search"),
                    row.get("raw_channel"),
                    row.get("raw_origin"),
                ),
            )
            inserted += 1
    return {"upserted": inserted}
