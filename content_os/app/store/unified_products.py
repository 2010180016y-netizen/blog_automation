from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

SOURCE_MY_STORE = "MY_STORE"
SOURCE_AFFILIATE = "AFFILIATE_SHOPPING_CONNECT"
SOURCE_BRAND_ANALYTICS = "MY_BRANDSTORE_ANALYTICS"

AFFILIATE_PRICE_NOTE_KO = "가격/혜택은 변동될 수 있습니다(작성일 기준). 최신 정보는 링크에서 확인하세요."


def ensure_unified_products_table(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                source_type TEXT NOT NULL,
                name TEXT,
                price INTEGER,
                shipping TEXT,
                product_link TEXT,
                options TEXT,
                as_info TEXT,
                prohibited_expressions TEXT,
                mandatory_disclaimer TEXT,
                evidence_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _load_my_store_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT sku, name, price, shipping, product_link, raw_channel, raw_origin, updated_at
        FROM products_ssot
        """
    ).fetchall()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "sku": r["sku"],
                "source_type": SOURCE_MY_STORE,
                "name": r["name"],
                "price": r["price"],
                "shipping": r["shipping"] or "",
                "product_link": r["product_link"],
                "options": "{}",
                "as_info": "",
                "mandatory_disclaimer": "",
                "evidence_data": json.dumps(
                    {
                        "raw_channel": r["raw_channel"],
                        "raw_origin": r["raw_origin"],
                        "ssot_updated_at": r["updated_at"],
                    },
                    ensure_ascii=False,
                ),
            }
        )
    return result


def _load_affiliate_rows(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT partner_product_id, title, affiliate_link, commission_note, updated_at
        FROM partner_products
        WHERE source = 'shopping_connect'
        """
    ).fetchall()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "sku": r["partner_product_id"],
                "source_type": SOURCE_AFFILIATE,
                "name": r["title"],
                "price": None,
                "shipping": "",
                "product_link": r["affiliate_link"],
                "options": "{}",
                "as_info": "",
                "mandatory_disclaimer": (r["commission_note"] or AFFILIATE_PRICE_NOTE_KO),
                "evidence_data": json.dumps(
                    {
                        "source": "shopping_connect",
                        "ssot_updated_at": r["updated_at"],
                        "policy": "affiliate_link_is_ssot",
                    },
                    ensure_ascii=False,
                ),
            }
        )
    return result


def _existing_map(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT sku, source_type, price, shipping, product_link FROM products").fetchall()
    return {r["sku"]: dict(r) for r in rows}


def sync_unified_products(db_path: str, refresh_queue_path: str | None = None) -> Dict[str, Any]:
    ensure_unified_products_table(db_path)
    with sqlite3.connect(db_path) as conn:
        existing = _existing_map(conn)

        rows = _load_my_store_rows(conn) + _load_affiliate_rows(conn)
        upserted = 0
        refresh_candidates: List[str] = []

        for row in rows:
            sku = row["sku"]
            prev = existing.get(sku)
            if prev and row["source_type"] == SOURCE_MY_STORE:
                changed = (
                    prev.get("price") != row.get("price")
                    or str(prev.get("shipping") or "") != str(row.get("shipping") or "")
                    or str(prev.get("product_link") or "") != str(row.get("product_link") or "")
                )
                if changed:
                    refresh_candidates.append(sku)

            conn.execute(
                """
                INSERT INTO products(
                    sku, source_type, name, price, shipping, product_link, options,
                    as_info, prohibited_expressions, mandatory_disclaimer, evidence_data,
                    created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(sku) DO UPDATE SET
                    source_type=excluded.source_type,
                    name=excluded.name,
                    price=excluded.price,
                    shipping=excluded.shipping,
                    product_link=excluded.product_link,
                    options=excluded.options,
                    as_info=excluded.as_info,
                    mandatory_disclaimer=excluded.mandatory_disclaimer,
                    evidence_data=excluded.evidence_data,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    row["sku"],
                    row["source_type"],
                    row.get("name"),
                    row.get("price"),
                    row.get("shipping"),
                    row.get("product_link"),
                    row.get("options", "{}"),
                    row.get("as_info", ""),
                    row.get("prohibited_expressions", ""),
                    row.get("mandatory_disclaimer", ""),
                    row.get("evidence_data", "{}"),
                    None,
                ),
            )
            upserted += 1

    refresh_report = {"count": len(sorted(set(refresh_candidates))), "skus": sorted(set(refresh_candidates))}
    if refresh_queue_path:
        p = Path(refresh_queue_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(refresh_report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"upserted": upserted, "refresh_queue": refresh_report}
