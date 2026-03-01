import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Set


class QueueState(str, Enum):
    DRAFT = "DRAFT"
    QA_PASS = "QA_PASS"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


@dataclass
class TransitionResult:
    item_id: int
    from_state: QueueState
    to_state: QueueState
    transitioned_at: str


class ContentQueueStateMachine:
    TRANSITIONS: Dict[QueueState, Set[QueueState]] = {
        QueueState.DRAFT: {QueueState.QA_PASS, QueueState.REJECTED},
        QueueState.QA_PASS: {QueueState.READY, QueueState.REJECTED},
        QueueState.READY: {QueueState.PUBLISHED, QueueState.REJECTED},
        QueueState.REJECTED: set(),
        QueueState.PUBLISHED: set(),
    }

    @classmethod
    def can_transition(cls, current: QueueState, nxt: QueueState) -> bool:
        return nxt in cls.TRANSITIONS.get(current, set())

    @classmethod
    def validate(cls, current: QueueState, nxt: QueueState):
        if not cls.can_transition(current, nxt):
            raise ValueError(f"Invalid transition: {current} -> {nxt}")


class ContentQueueService:
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
                CREATE TABLE IF NOT EXISTS content_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    disclosure_required INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'DRAFT',
                    payload TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sku, intent, source_type)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS queue_transition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id INTEGER NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    note TEXT,
                    transitioned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
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

    def create_item(self, sku: str, intent: str, source_type: str, disclosure_required: bool = True, payload: Optional[dict] = None) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO content_queue (sku, intent, source_type, disclosure_required, status, payload, updated_at)
                VALUES (?, ?, ?, ?, 'DRAFT', ?, CURRENT_TIMESTAMP)
                """,
                (sku, intent, source_type, 1 if disclosure_required else 0, json.dumps(payload or {}, ensure_ascii=False)),
            )
            return int(cur.lastrowid)

    def _load_state(self, status: str) -> QueueState:
        if status == "PENDING":
            return QueueState.DRAFT
        return QueueState(status)

    def get_item(self, item_id: int) -> sqlite3.Row:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM content_queue WHERE id = ?", (item_id,)).fetchone()
            if not row:
                raise ValueError("Queue item not found")
            return row

    def transition(self, item_id: int, next_state: QueueState, note: Optional[str] = None) -> TransitionResult:
        with self._connect() as conn:
            row = conn.execute("SELECT id, sku, status FROM content_queue WHERE id = ?", (item_id,)).fetchone()
            if not row:
                raise ValueError("Queue item not found")

            current = self._load_state(row["status"])
            if current == QueueState.PUBLISHED:
                raise ValueError("Cannot overwrite PUBLISHED content directly; enqueue refresh_queue instead")

            ContentQueueStateMachine.validate(current, next_state)

            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE content_queue SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (next_state.value, item_id),
            )
            conn.execute(
                "INSERT INTO queue_transition_history (queue_id, from_state, to_state, note) VALUES (?, ?, ?, ?)",
                (item_id, current.value, next_state.value, note),
            )

            return TransitionResult(
                item_id=item_id,
                from_state=current,
                to_state=next_state,
                transitioned_at=now,
            )

    def request_refresh_for_published(self, item_id: int, reason: str, payload: Optional[dict] = None) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT id, sku, status FROM content_queue WHERE id = ?", (item_id,)).fetchone()
            if not row:
                raise ValueError("Queue item not found")
            current = self._load_state(row["status"])
            if current != QueueState.PUBLISHED:
                raise ValueError("Refresh queue is only for already PUBLISHED content")

            cur = conn.execute(
                "INSERT INTO refresh_queue (sku, reason, payload, status) VALUES (?, ?, ?, 'PENDING')",
                (row["sku"], reason, json.dumps(payload or {}, ensure_ascii=False)),
            )
            return int(cur.lastrowid)
