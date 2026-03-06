from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import httpx


@dataclass
class ShoppingConnectRow:
    partner_product_id: str
    title: str
    affiliate_link: str
    category: str = ""
    keywords: str = ""
    content_type: str = "review"
    source: str = "shopping_connect"
    usage_mode: str = "commercial"


ALLOWED_CONTENT_TYPES = {"landing", "review", "comparison", "shorts"}


def _is_valid_http_url(value: str) -> bool:
    try:
        p = urlparse(value)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def load_rows_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_rows_from_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_rows_from_google_sheet_csv(csv_url: str) -> List[Dict[str, Any]]:
    with urlopen(csv_url, timeout=10.0) as r:  # nosec B310
        raw = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(raw)))


def normalize_rows(raw_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for r in raw_rows:
        item = ShoppingConnectRow(
            partner_product_id=str(r.get("partner_product_id") or r.get("id") or r.get("sku") or "").strip(),
            title=str(r.get("title") or r.get("name") or "").strip(),
            affiliate_link=str(r.get("affiliate_link") or r.get("link") or "").strip(),
            category=str(r.get("category") or "").strip(),
            keywords=str(r.get("keywords") or "").strip(),
            content_type=str(r.get("content_type") or "review").strip().lower(),
            source=str(r.get("source") or "shopping_connect").strip().lower(),
            usage_mode=str(r.get("usage_mode") or "commercial").strip().lower(),
        )
        normalized.append(item.__dict__)
    return normalized


def validate_shopping_connect_rows(rows: List[Dict[str, Any]], check_link_live: bool = False) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []

    for i, row in enumerate(rows):
        rid = row.get("partner_product_id") or f"row_{i+1}"

        if row.get("source") != "shopping_connect":
            errors.append({"id": rid, "reason": "source must be shopping_connect"})
        if row.get("usage_mode") != "commercial":
            errors.append({"id": rid, "reason": "usage_mode must be commercial for monetization flow"})
        if not row.get("partner_product_id"):
            errors.append({"id": rid, "reason": "missing partner_product_id"})
        if not row.get("affiliate_link") or not _is_valid_http_url(row.get("affiliate_link", "")):
            errors.append({"id": rid, "reason": "invalid affiliate_link"})
        if row.get("content_type") not in ALLOWED_CONTENT_TYPES:
            errors.append({"id": rid, "reason": f"invalid content_type (allowed: {sorted(ALLOWED_CONTENT_TYPES)})"})

        if check_link_live and row.get("affiliate_link") and _is_valid_http_url(row.get("affiliate_link", "")):
            try:
                with httpx.Client(timeout=7.0, follow_redirects=True) as client:
                    res = client.get(row["affiliate_link"])
                    if res.status_code >= 400:
                        errors.append({"id": rid, "reason": f"affiliate_link unreachable status={res.status_code}"})
            except Exception as exc:
                errors.append({"id": rid, "reason": f"affiliate_link unreachable: {exc}"})

    return {"status": "PASS" if not errors else "REJECT", "errors": errors}
