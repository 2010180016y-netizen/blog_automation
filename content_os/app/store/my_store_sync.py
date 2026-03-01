import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TokenState:
    access_token: str
    expires_at: datetime


class MyStoreRepository:
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
                CREATE TABLE IF NOT EXISTS my_store_products (
                    sku TEXT PRIMARY KEY,
                    product_id TEXT,
                    title TEXT,
                    price REAL,
                    currency TEXT,
                    status TEXT,
                    payload_hash TEXT,
                    raw_json TEXT,
                    parse_status TEXT NOT NULL,
                    parse_error TEXT,
                    source TEXT NOT NULL DEFAULT 'MY_STORE',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS refresh_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    payload TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # 대량 upsert/조회 병목 완화를 위한 인덱스
            conn.execute("CREATE INDEX IF NOT EXISTS idx_my_store_products_product_id ON my_store_products(product_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_my_store_products_payload_hash ON my_store_products(payload_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_refresh_queue_sku_status ON refresh_queue(sku, status)")

    def get_hashes(self, skus: List[str]) -> Dict[str, str]:
        if not skus:
            return {}
        placeholders = ",".join("?" for _ in skus)
        query = f"SELECT sku, payload_hash FROM my_store_products WHERE sku IN ({placeholders})"
        with self._connect() as conn:
            rows = conn.execute(query, skus).fetchall()
        return {row["sku"]: row["payload_hash"] for row in rows}

    def batch_upsert_products(self, rows: List[Dict[str, Any]], chunk_size: int = 500) -> int:
        if not rows:
            return 0
        sql = (
            "INSERT INTO my_store_products "
            "(sku, product_id, title, price, currency, status, payload_hash, raw_json, parse_status, parse_error, source, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'MY_STORE', CURRENT_TIMESTAMP) "
            "ON CONFLICT(sku) DO UPDATE SET "
            "product_id=excluded.product_id, "
            "title=excluded.title, "
            "price=excluded.price, "
            "currency=excluded.currency, "
            "status=excluded.status, "
            "payload_hash=excluded.payload_hash, "
            "raw_json=excluded.raw_json, "
            "parse_status=excluded.parse_status, "
            "parse_error=excluded.parse_error, "
            "updated_at=CURRENT_TIMESTAMP"
        )
        params = [
            (
                r.get("sku"),
                r.get("product_id"),
                r.get("title"),
                r.get("price"),
                r.get("currency"),
                r.get("status"),
                r.get("payload_hash"),
                r.get("raw_json"),
                r.get("parse_status"),
                r.get("parse_error"),
            )
            for r in rows
        ]
        with self._connect() as conn:
            conn.execute("BEGIN")
            for start in range(0, len(params), chunk_size):
                conn.executemany(sql, params[start : start + chunk_size])
            conn.commit()
        return len(rows)

    def enqueue_refresh(self, entries: List[Tuple[str, str, Dict[str, Any]]]) -> int:
        if not entries:
            return 0
        sql = "INSERT INTO refresh_queue (sku, reason, payload, status) VALUES (?, ?, ?, 'PENDING')"
        params = [(sku, reason, json.dumps(payload, ensure_ascii=False)) for sku, reason, payload in entries]
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.executemany(sql, params)
            conn.commit()
        return len(entries)


class MyStoreSyncService:
    def __init__(
        self,
        repo: MyStoreRepository,
        client: Optional[httpx.Client] = None,
        now_fn=None,
        sleep_fn=None,
        max_retries: int = 3,
        backoff_seconds: float = 0.3,
        concurrency: int = 5,
        page_size: int = 50,
    ):
        self.repo = repo
        self.client = client or httpx.Client(timeout=20)
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.sleep_fn = sleep_fn or time.sleep
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.page_size = page_size
        self.concurrency = max(1, int(concurrency))
        self.semaphore = threading.Semaphore(self.concurrency)
        self._token_state: Optional[TokenState] = None

        self.token_url = os.getenv("NAVER_COMMERCE_TOKEN_URL", "")
        self.api_base_url = os.getenv("NAVER_COMMERCE_API_BASE_URL", "")
        self.client_id = os.getenv("NAVER_COMMERCE_CLIENT_ID", "")
        self.client_secret = os.getenv("NAVER_COMMERCE_CLIENT_SECRET", "")

    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        retriable = {408, 409, 425, 429, 500, 502, 503, 504}
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.client.request(method, url, **kwargs)
                if resp.status_code in retriable and attempt < self.max_retries:
                    backoff = self.backoff_seconds * (2**attempt)
                    logger.warning("Retrying %s %s after status=%s in %.2fs", method, url, resp.status_code, backoff)
                    self.sleep_fn(backoff)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    raise
                backoff = self.backoff_seconds * (2**attempt)
                logger.warning("Retrying %s %s after exception=%s in %.2fs", method, url, type(exc).__name__, backoff)
                self.sleep_fn(backoff)
        if last_exc:
            raise last_exc
        raise RuntimeError("Unknown retry failure")

    def _token_valid(self) -> bool:
        if not self._token_state:
            return False
        return self.now_fn() < (self._token_state.expires_at - timedelta(seconds=60))

    def get_access_token(self) -> str:
        if self._token_valid():
            return self._token_state.access_token

        if not self.token_url:
            raise ValueError("NAVER_COMMERCE_TOKEN_URL is required")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        t0 = time.perf_counter()
        resp = self._request_with_retry("POST", self.token_url, data=data)
        payload = resp.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not token:
            raise ValueError("Token response missing access_token")

        self._token_state = TokenState(
            access_token=token,
            expires_at=self.now_fn() + timedelta(seconds=expires_in),
        )
        logger.info("my_store.token_fetch_sec=%.3f", time.perf_counter() - t0)
        return token

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def fetch_product_ids(self) -> List[str]:
        if not self.api_base_url:
            raise ValueError("NAVER_COMMERCE_API_BASE_URL is required")

        t0 = time.perf_counter()
        ids: List[str] = []
        page = 1
        cursor = None
        while True:
            params: Dict[str, Any] = {"page_size": self.page_size}
            if cursor:
                params["cursor"] = cursor
            else:
                params["page"] = page

            url = f"{self.api_base_url.rstrip('/')}/products"
            resp = self._request_with_retry("GET", url, headers=self._auth_headers(), params=params)
            data = resp.json()

            items = data.get("products") or data.get("items") or data.get("content") or []
            for it in items:
                pid = it.get("id") or it.get("product_id") or it.get("productNo")
                if pid is not None:
                    ids.append(str(pid))

            has_more = bool(data.get("has_more"))
            next_cursor = data.get("next_cursor") or data.get("nextCursor")
            total_pages = data.get("total_pages")

            if next_cursor:
                cursor = str(next_cursor)
                continue
            if has_more:
                page += 1
                continue
            if total_pages and page < int(total_pages):
                page += 1
                continue
            break
        logger.info("my_store.fetch_ids_sec=%.3f count=%d", time.perf_counter() - t0, len(ids))
        return ids

    def fetch_product_detail(self, product_id: str) -> Dict[str, Any]:
        url = f"{self.api_base_url.rstrip('/')}/products/{product_id}"
        with self.semaphore:
            resp = self._request_with_retry("GET", url, headers=self._auth_headers())
            return resp.json()

    @staticmethod
    def _hash_payload(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def parse_product(self, product_id: str, detail: Dict[str, Any]) -> Dict[str, Any]:
        raw_json = json.dumps(detail, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        try:
            sku = detail.get("sku") or detail.get("sellerManagementCode") or detail.get("id") or product_id
            if not sku:
                raise ValueError("missing sku")

            return {
                "sku": str(sku),
                "product_id": str(product_id),
                "title": detail.get("name") or detail.get("title") or "",
                "price": detail.get("price") or detail.get("salePrice") or 0,
                "currency": detail.get("currency") or "KRW",
                "status": detail.get("status") or "UNKNOWN",
                "raw_json": raw_json,
                "payload_hash": self._hash_payload(raw_json),
                "parse_status": "OK",
                "parse_error": None,
            }
        except Exception as exc:
            logger.warning("Failed to parse product %s: %s", product_id, exc)
            fallback_sku = str(product_id)
            return {
                "sku": fallback_sku,
                "product_id": str(product_id),
                "title": "",
                "price": 0,
                "currency": "KRW",
                "status": "PARSE_FAIL",
                "raw_json": raw_json,
                "payload_hash": self._hash_payload(raw_json),
                "parse_status": "PARSE_FAIL",
                "parse_error": str(exc),
            }

    def _build_refresh_entries(self, rows: List[Dict[str, Any]]) -> List[Tuple[str, str, Dict[str, Any]]]:
        hashes = self.repo.get_hashes([r["sku"] for r in rows])
        entries: List[Tuple[str, str, Dict[str, Any]]] = []
        for r in rows:
            old_hash = hashes.get(r["sku"])
            if old_hash is None:
                entries.append((r["sku"], "NEW_PRODUCT", {"product_id": r["product_id"]}))
            elif old_hash != r["payload_hash"]:
                entries.append((r["sku"], "PRODUCT_CHANGED", {"product_id": r["product_id"]}))
        return entries

    def sync(self) -> Dict[str, Any]:
        total_start = time.perf_counter()

        t_ids = time.perf_counter()
        product_ids = self.fetch_product_ids()
        ids_sec = time.perf_counter() - t_ids

        parsed_rows: List[Dict[str, Any]] = []
        errors = 0

        t_details = time.perf_counter()
        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            futures = {ex.submit(self.fetch_product_detail, pid): pid for pid in product_ids}
            for fut in as_completed(futures):
                pid = futures[fut]
                try:
                    detail = fut.result()
                    parsed_rows.append(self.parse_product(pid, detail))
                except Exception as exc:
                    errors += 1
                    logger.error("Detail fetch failed for product_id=%s; check API auth/rate-limit/payload. error=%s", pid, exc)
        details_sec = time.perf_counter() - t_details

        t_upsert = time.perf_counter()
        refresh_entries = self._build_refresh_entries(parsed_rows)
        upserted = self.repo.batch_upsert_products(parsed_rows)
        queued = self.repo.enqueue_refresh(refresh_entries)
        db_sec = time.perf_counter() - t_upsert

        total_sec = time.perf_counter() - total_start
        logger.info(
            "my_store.sync_sec=%.3f ids_sec=%.3f details_sec=%.3f db_sec=%.3f fetched=%d upserted=%d queued=%d errors=%d",
            total_sec,
            ids_sec,
            details_sec,
            db_sec,
            len(product_ids),
            upserted,
            queued,
            errors,
        )

        return {
            "fetched": len(product_ids),
            "upserted": upserted,
            "queued": queued,
            "errors": errors,
            "timings": {
                "fetch_ids_sec": round(ids_sec, 6),
                "fetch_details_sec": round(details_sec, 6),
                "db_upsert_enqueue_sec": round(db_sec, 6),
                "total_sec": round(total_sec, 6),
            },
        }
