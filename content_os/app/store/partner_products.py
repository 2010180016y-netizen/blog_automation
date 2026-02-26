from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


DISALLOWED_COMMERCIAL_SOURCES = {"naver_shopping_openapi", "shopping_search_api"}
ALLOWED_PARTNER_SOURCE = "shopping_connect"


def validate_partner_product_source(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations: List[Dict[str, str]] = []

    for item in products:
        source = str(item.get("source") or "").lower()
        usage = str(item.get("usage_mode") or "commercial").lower()
        if usage == "commercial" and source in DISALLOWED_COMMERCIAL_SOURCES:
            violations.append(
                {
                    "product_id": str(item.get("id") or item.get("sku") or ""),
                    "source": source,
                    "reason": "commercial reuse of shopping search results is restricted; use Shopping Connect links",
                }
            )

    return {
        "status": "PASS" if not violations else "REJECT",
        "violations": violations,
    }


def ensure_partner_table(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS partner_products (
                partner_product_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT,
                category TEXT,
                affiliate_link TEXT NOT NULL,
                advertiser TEXT,
                commission_note TEXT,
                usage_mode TEXT DEFAULT 'commercial',
                raw_payload TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_partner_products(db_path: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
    validation = validate_partner_product_source(products)
    if validation["status"] == "REJECT":
        return {"upserted": 0, "validation": validation}

    ensure_partner_table(db_path)
    upserted = 0
    with sqlite3.connect(db_path) as conn:
        for p in products:
            conn.execute(
                """
                INSERT INTO partner_products(
                    partner_product_id, source, title, category, affiliate_link,
                    advertiser, commission_note, usage_mode, raw_payload, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(partner_product_id) DO UPDATE SET
                    source=excluded.source,
                    title=excluded.title,
                    category=excluded.category,
                    affiliate_link=excluded.affiliate_link,
                    advertiser=excluded.advertiser,
                    commission_note=excluded.commission_note,
                    usage_mode=excluded.usage_mode,
                    raw_payload=excluded.raw_payload,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    p.get("partner_product_id") or p.get("id") or p.get("sku"),
                    p.get("source", ALLOWED_PARTNER_SOURCE),
                    p.get("title") or p.get("name"),
                    p.get("category"),
                    p.get("affiliate_link"),
                    p.get("advertiser"),
                    p.get("commission_note"),
                    p.get("usage_mode", "commercial"),
                    json.dumps(p, ensure_ascii=False),
                ),
            )
            upserted += 1

    return {"upserted": upserted, "validation": validation}


def build_two_track_ssot(db_path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        own_rows = conn.execute(
            """
            SELECT sku, name, price, product_link, 'own_store' AS track, updated_at
            FROM products_ssot
            """
        ).fetchall()
        partner_rows = conn.execute(
            """
            SELECT partner_product_id AS sku, title AS name, NULL AS price,
                   affiliate_link AS product_link, 'partner_store' AS track, updated_at
            FROM partner_products
            WHERE source = ?
            """,
            (ALLOWED_PARTNER_SOURCE,),
        ).fetchall()

        for r in list(own_rows) + list(partner_rows):
            rows.append(dict(r))

    return rows


def export_two_track_ssot(db_path: str, output_json_path: str) -> Dict[str, Any]:
    merged = build_two_track_ssot(db_path)
    path = Path(output_json_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(path), "count": len(merged)}
