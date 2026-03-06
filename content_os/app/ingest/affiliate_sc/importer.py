from __future__ import annotations

import csv
from typing import Dict, List

from ...store.partner_products import upsert_partner_products
from ...store.shopping_connect_ingest import normalize_rows, validate_shopping_connect_rows


def import_affiliate_links_from_csv(db_path: str, csv_path: str, check_link_live: bool = False) -> Dict:
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        raw = list(csv.DictReader(f))

    rows = normalize_rows(raw)
    validation = validate_shopping_connect_rows(rows, check_link_live=check_link_live)
    if validation["status"] == "REJECT":
        return {"status": "REJECT", "validation": validation, "upserted": 0}

    upsert = upsert_partner_products(db_path, rows)
    return {"status": "PASS", "validation": validation, **upsert}


def create_content_queue_candidates(rows: List[Dict]) -> List[Dict]:
    content_types = ["information", "comparison", "review", "story"]
    queue = []
    for row in rows:
        for ctype in content_types[:2]:  # at least 2 types
            queue.append(
                {
                    "sku": row.get("partner_product_id"),
                    "source_type": "AFFILIATE_SC",
                    "content_type": ctype,
                    "title_seed": row.get("title"),
                }
            )
    return queue
