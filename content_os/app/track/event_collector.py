import sqlite3
import json
from datetime import datetime
from typing import Dict, List

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
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events (event_type, channel, content_id, sku, intent, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (event_type, channel, content_id, sku, intent, json.dumps(metadata or {}))
            )

    def get_events(self, filters: Dict = None) -> List[Dict]:
        query = "SELECT * FROM events"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
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
