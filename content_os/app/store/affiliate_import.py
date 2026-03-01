import csv
import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


VALID_INTENTS = {"info", "compare", "review", "buy"}
DEFAULT_QUEUE_INTENTS = ["info", "compare"]


@dataclass
class AffiliateRow:
    sku: str
    product_name: str
    affiliate_url: str
    price: Optional[float] = None
    currency: str = "KRW"


class AffiliateImportRepository:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    sku TEXT PRIMARY KEY,
                    product_name TEXT,
                    affiliate_url TEXT,
                    price REAL,
                    currency TEXT,
                    source_type TEXT NOT NULL,
                    disclosure_required INTEGER NOT NULL DEFAULT 1,
                    raw_json TEXT,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    disclosure_required INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    payload TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sku, intent, source_type)
                )
                """
            )

    def upsert_products(self, products: List[AffiliateRow]) -> int:
        if not products:
            return 0
        sql = (
            "INSERT INTO products (sku, product_name, affiliate_url, price, currency, source_type, disclosure_required, raw_json, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'AFFILIATE_SC', 1, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(sku) DO UPDATE SET "
            "product_name=excluded.product_name, "
            "affiliate_url=excluded.affiliate_url, "
            "price=excluded.price, "
            "currency=excluded.currency, "
            "source_type='AFFILIATE_SC', "
            "disclosure_required=1, "
            "raw_json=excluded.raw_json, "
            "updated_at=CURRENT_TIMESTAMP"
        )
        rows = [
            (
                p.sku,
                p.product_name,
                p.affiliate_url,
                p.price,
                p.currency,
                json.dumps(p.__dict__, ensure_ascii=False),
            )
            for p in products
        ]
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.executemany(sql, rows)
            conn.commit()
        return len(products)

    def enqueue_content(self, products: List[AffiliateRow], intents: List[str]) -> int:
        if not products:
            return 0
        intents = list(dict.fromkeys(intents))
        valid_intents = [i for i in intents if i in VALID_INTENTS]
        if not valid_intents:
            valid_intents = DEFAULT_QUEUE_INTENTS

        sql = (
            "INSERT OR IGNORE INTO content_queue "
            "(sku, intent, source_type, disclosure_required, status, payload) "
            "VALUES (?, ?, 'AFFILIATE_SC', 1, 'PENDING', ?)"
        )
        rows = []
        for p in products:
            for intent in valid_intents:
                rows.append((p.sku, intent, json.dumps({"affiliate_url": p.affiliate_url}, ensure_ascii=False)))

        with self._connect() as conn:
            before = conn.execute(
                "SELECT COUNT(*) FROM content_queue WHERE source_type='AFFILIATE_SC'"
            ).fetchone()[0]
            conn.execute("BEGIN")
            conn.executemany(sql, rows)
            conn.commit()
            after = conn.execute(
                "SELECT COUNT(*) FROM content_queue WHERE source_type='AFFILIATE_SC'"
            ).fetchone()[0]
        return int(after - before)


def _normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.strip().lower())


def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def _coerce_price(v: str) -> Optional[float]:
    if v is None or str(v).strip() == "":
        return None
    return float(str(v).replace(",", "").strip())


def parse_affiliate_csv(csv_path: str) -> Tuple[List[AffiliateRow], List[Dict[str, Any]]]:
    rows: List[AffiliateRow] = []
    errors: List[Dict[str, Any]] = []
    seen = set()

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV header is missing")

        header_map = {_normalize_header(h): h for h in reader.fieldnames}

        sku_key = header_map.get("sku") or header_map.get("productsku")
        name_key = header_map.get("productname") or header_map.get("name") or header_map.get("title")
        url_key = header_map.get("affiliateurl") or header_map.get("url") or header_map.get("link")
        price_key = header_map.get("price")
        currency_key = header_map.get("currency")

        if not (sku_key and name_key and url_key):
            raise ValueError("CSV requires sku, product_name(name/title), affiliate_url(url/link) columns")

        for i, r in enumerate(reader, start=2):
            sku = (r.get(sku_key) or "").strip()
            name = (r.get(name_key) or "").strip()
            url = (r.get(url_key) or "").strip()
            cur = (r.get(currency_key) or "KRW").strip() if currency_key else "KRW"

            if not sku or not name or not url:
                errors.append({"line": i, "error": "missing_required_field", "sku": sku})
                continue
            if not _is_valid_url(url):
                errors.append({"line": i, "error": "invalid_url", "sku": sku})
                continue

            key = (sku, url)
            if key in seen:
                continue
            seen.add(key)

            try:
                price = _coerce_price(r.get(price_key)) if price_key else None
            except ValueError:
                errors.append({"line": i, "error": "invalid_price", "sku": sku})
                continue

            rows.append(AffiliateRow(sku=sku, product_name=name, affiliate_url=url, price=price, currency=cur or "KRW"))

    return rows, errors


def import_affiliate_csv(
    csv_path: str,
    db_path: str = "blogs.db",
    intents: Optional[List[str]] = None,
) -> Dict[str, Any]:
    intents = intents or DEFAULT_QUEUE_INTENTS
    parsed, errors = parse_affiliate_csv(csv_path)

    repo = AffiliateImportRepository(db_path=db_path)
    upserted = repo.upsert_products(parsed)
    queued = repo.enqueue_content(parsed, intents=intents)

    return {
        "input_file": csv_path,
        "parsed": len(parsed),
        "errors": errors,
        "upserted": upserted,
        "queued": queued,
        "intents": intents,
        "source_type": "AFFILIATE_SC",
        "disclosure_required_default": True,
    }
