import json
import sqlite3
from typing import Dict, List, Optional

from ..store.commerce_ssot import ensure_ssot_table, upsert_ssot_rows
from ..store.unified_products import sync_unified_products
from .models import ContentEntry

REFRESH_PENDING = "PENDING"
REFRESH_PROCESSING = "PROCESSING"
REFRESH_DONE = "DONE"
REFRESH_FAILED = "FAILED"


class RefreshQueueStateMachine:
    TRANSITIONS = {
        REFRESH_PENDING: {REFRESH_PROCESSING, REFRESH_FAILED},
        REFRESH_PROCESSING: {REFRESH_DONE, REFRESH_FAILED, REFRESH_PENDING},
        REFRESH_FAILED: {REFRESH_PENDING, REFRESH_PROCESSING},
        REFRESH_DONE: {REFRESH_PENDING},
    }

    @classmethod
    def validate(cls, current: str, nxt: str) -> None:
        if nxt not in cls.TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid refresh queue transition: {current} -> {nxt}")


def ensure_refresh_queue_table(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_queue (
                sku TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'PENDING',
                reason TEXT NOT NULL DEFAULT 'PRODUCT_CHANGED',
                payload TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                enqueued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cols = {row[1] for row in conn.execute("PRAGMA table_info(refresh_queue)").fetchall()}
        if "retry_count" not in cols:
            conn.execute("ALTER TABLE refresh_queue ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0")
        if "last_error" not in cols:
            conn.execute("ALTER TABLE refresh_queue ADD COLUMN last_error TEXT")


class ContentRepo:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    paragraphs TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_content(self, entry: ContentEntry):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO contents (content, paragraphs, metadata) VALUES (?, ?, ?)",
                (entry.content, json.dumps(entry.paragraphs), json.dumps(entry.metadata)),
            )
            return cursor.lastrowid

    def get_all_paragraphs(self) -> List[str]:
        all_paras = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT paragraphs FROM contents")
            for row in cursor:
                all_paras.extend(json.loads(row[0]))
        return all_paras

    def get_all_entries(self) -> List[ContentEntry]:
        entries = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, content, paragraphs, metadata, created_at FROM contents")
            for row in cursor:
                entries.append(
                    ContentEntry(
                        id=row[0],
                        content=row[1],
                        paragraphs=json.loads(row[2]),
                        metadata=json.loads(row[3]),
                        created_at=row[4],
                    )
                )
        return entries


class ProductRepo:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        ensure_ssot_table(self.db_path)
        ensure_refresh_queue_table(self.db_path)

    def upsert_products_ssot(self, rows: List[Dict]) -> Dict[str, int]:
        return upsert_ssot_rows(self.db_path, rows)

    def sync_unified_products_with_refresh(self) -> Dict:
        return sync_unified_products(self.db_path)

    def enqueue_refresh_candidates(self, skus: List[str], reason: str = "PRODUCT_CHANGED") -> Dict[str, int]:
        if not skus:
            return {"enqueued": 0}

        unique_skus = sorted(set(skus))
        with sqlite3.connect(self.db_path) as conn:
            for sku in unique_skus:
                conn.execute(
                    """
                    INSERT INTO refresh_queue (sku, status, reason, payload, retry_count, last_error, enqueued_at, updated_at)
                    VALUES (?, 'PENDING', ?, ?, 0, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(sku) DO UPDATE SET
                        status='PENDING',
                        reason=excluded.reason,
                        payload=excluded.payload,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (sku, reason, json.dumps({"sku": sku, "reason": reason}, ensure_ascii=False)),
                )

        return {"enqueued": len(unique_skus)}

    def _set_refresh_status(self, sku: str, next_status: str, error: Optional[str] = None, increment_retry: bool = False) -> None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT status, retry_count FROM refresh_queue WHERE sku=?", (sku,)).fetchone()
            if not row:
                raise ValueError(f"Refresh queue item not found: {sku}")
            current = str(row[0])
            RefreshQueueStateMachine.validate(current, next_status)

            retry_sql = "retry_count = retry_count + 1" if increment_retry else "retry_count = retry_count"
            conn.execute(
                f"""
                UPDATE refresh_queue
                SET status=?, last_error=?, {retry_sql}, updated_at=CURRENT_TIMESTAMP
                WHERE sku=?
                """,
                (next_status, error, sku),
            )

    def mark_refresh_processing(self, sku: str) -> None:
        self._set_refresh_status(sku, REFRESH_PROCESSING)

    def mark_refresh_failed(self, sku: str, error: str) -> None:
        self._set_refresh_status(sku, REFRESH_FAILED, error=error, increment_retry=True)

    def mark_refresh_done(self, sku: str) -> None:
        self._set_refresh_status(sku, REFRESH_DONE)

    def requeue_refresh_item(self, sku: str) -> None:
        self._set_refresh_status(sku, REFRESH_PENDING)

    def get_refresh_queue(self, status: str = REFRESH_PENDING) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT sku, status, reason, payload, retry_count, last_error, enqueued_at, updated_at FROM refresh_queue WHERE status=? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_refresh_queue_skus(self) -> List[str]:
        return [row["sku"] for row in self.get_refresh_queue(status=REFRESH_PENDING)]
