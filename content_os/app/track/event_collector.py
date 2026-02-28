import sqlite3
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

ALLOWED_FILTER_COLUMNS = {
    "id", "event_type", "channel", "content_id", "sku", "intent", "timestamp"
}

audit_logger = logging.getLogger("content_os.audit")

SENSITIVE_KEYWORDS = {
    "email", "mail", "phone", "mobile", "name", "fullname",
    "address", "ip", "user", "userid", "user_id", "personal", "resident"
}


def _is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return any(keyword in normalized for keyword in SENSITIVE_KEYWORDS)


def _sanitize_metadata(value: Any, path: str = "") -> Tuple[Any, List[str]]:
    dropped_keys: List[str] = []

    if isinstance(value, dict):
        sanitized = {}
        for key, nested_value in value.items():
            key_str = str(key)
            nested_path = f"{path}.{key_str}" if path else key_str

            if _is_sensitive_key(key_str):
                dropped_keys.append(nested_path)
                continue

            sanitized_value, nested_dropped = _sanitize_metadata(nested_value, nested_path)
            dropped_keys.extend(nested_dropped)
            sanitized[key] = sanitized_value

        return sanitized, dropped_keys

    if isinstance(value, list):
        sanitized_list = []
        for idx, item in enumerate(value):
            nested_path = f"{path}[{idx}]" if path else f"[{idx}]"
            sanitized_item, nested_dropped = _sanitize_metadata(item, nested_path)
            dropped_keys.extend(nested_dropped)
            sanitized_list.append(sanitized_item)
        return sanitized_list, dropped_keys

    if isinstance(value, str):
        # Basic masking for accidental direct PII in free text values.
        masked = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted_email]", value)
        masked = re.sub(r"\b\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}\b", "[redacted_phone]", masked)
        return masked, dropped_keys

    return value, dropped_keys

class EventCollector:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    channel TEXT,
                    content_id TEXT,
                    sku TEXT,
                    intent TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def collect(self, event_type: str, channel: str, content_id: str, sku: str, intent: str, metadata: Dict = None):
        sanitized_metadata, dropped_keys = _sanitize_metadata(metadata or {})
        if dropped_keys:
            audit_logger.warning(json.dumps({
                "event": "PII_METADATA_KEYS_DROPPED",
                "content_id": content_id,
                "channel": channel,
                "dropped_keys": dropped_keys,
                "dropped_count": len(dropped_keys),
            }, ensure_ascii=False))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events (event_type, channel, content_id, sku, intent, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (event_type, channel, content_id, sku, intent, json.dumps(sanitized_metadata, ensure_ascii=False))
            )

    def purge_old_events(self, retention_days: int = 90) -> int:
        if retention_days <= 0:
            raise ValueError("retention_days must be greater than 0")

        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM events WHERE timestamp < ?",
                (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
            )
            return cursor.rowcount

    def get_events(self, filters: Dict = None) -> List[Dict]:
        query = "SELECT * FROM events"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
                if k not in ALLOWED_FILTER_COLUMNS:
                    raise ValueError(f"Unsupported filter column: {k}")
                conditions.append(f"{k} = ?")
                params.append(v)
            query += " WHERE " + " AND ".join(conditions)
            
        events = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            for row in cursor:
                events.append(dict(row))
        return events
