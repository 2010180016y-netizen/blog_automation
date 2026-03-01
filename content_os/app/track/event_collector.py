import sqlite3
import json
from typing import Dict, List, Optional


ALLOWED_EVENTS = {"page_view", "cta_click", "store_click"}
ALLOWED_FILTERS = {"event_type", "channel", "content_id", "sku", "intent"}


class EventCollector:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def collect(self, event_type: str, channel: str, content_id: str, sku: str, intent: str, metadata: Optional[Dict] = None):
        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Unsupported event_type: {event_type}")

        required = {
            "channel": channel,
            "content_id": content_id,
            "sku": sku,
            "intent": intent,
        }
        for k, v in required.items():
            if v is None or str(v).strip() == "":
                raise ValueError(f"{k} is required")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events (event_type, channel, content_id, sku, intent, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (event_type, channel, content_id, sku, intent, json.dumps(metadata or {})),
            )

    def get_events(self, filters: Optional[Dict] = None) -> List[Dict]:
        query = "SELECT * FROM events"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
                if k not in ALLOWED_FILTERS:
                    raise ValueError(f"Unsupported filter: {k}")
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
