import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Protocol

from .state_machine import ContentState, StateMachine


class QueueStorage(Protocol):
    def load_items(self) -> Dict[str, Dict]:
        ...

    def save_item(self, content_id: str, item: Dict) -> None:
        ...


class InMemoryQueueStorage:
    def __init__(self):
        self._items: Dict[str, Dict] = {}

    def load_items(self) -> Dict[str, Dict]:
        return self._items

    def save_item(self, content_id: str, item: Dict) -> None:
        self._items[content_id] = item


class SQLiteQueueStorage:
    def __init__(self, db_path: str = "publish_queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS publish_queue (
                    content_id TEXT PRIMARY KEY,
                    data TEXT,
                    state TEXT,
                    history TEXT,
                    human_approval_required INTEGER DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def load_items(self) -> Dict[str, Dict]:
        items: Dict[str, Dict] = {}
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT content_id, data, state, history, human_approval_required FROM publish_queue"
            )
            for row in cursor:
                item = {
                    "id": row["content_id"],
                    "data": json.loads(row["data"] or "{}"),
                    "state": ContentState(row["state"]),
                    "history": [ContentState(s) for s in json.loads(row["history"] or "[]")],
                    "human_approval_required": bool(row["human_approval_required"]),
                }
                items[row["content_id"]] = item
        return items

    def save_item(self, content_id: str, item: Dict) -> None:
        history_values = [state.value if isinstance(state, ContentState) else str(state) for state in item["history"]]
        state_value = item["state"].value if isinstance(item["state"], ContentState) else str(item["state"])

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO publish_queue (content_id, data, state, history, human_approval_required, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(content_id) DO UPDATE SET
                    data=excluded.data,
                    state=excluded.state,
                    history=excluded.history,
                    human_approval_required=excluded.human_approval_required,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    content_id,
                    json.dumps(item.get("data", {}), ensure_ascii=False),
                    state_value,
                    json.dumps(history_values),
                    1 if item.get("human_approval_required") else 0,
                ),
            )


class PublishQueue:
    def __init__(self, config: Dict, storage: Optional[QueueStorage] = None):
        self.config = config
        self.storage = storage or InMemoryQueueStorage()
        self.items: Dict[str, Dict] = self.storage.load_items()  # content_id -> item

    def _save_item(self, content_id: str):
        item = self.items.get(content_id)
        if item:
            self.storage.save_item(content_id, item)

    def add_item(self, content_id: str, data: Dict):
        self.items[content_id] = {
            "id": content_id,
            "data": data,
            "state": ContentState.DRAFT,
            "history": [ContentState.DRAFT],
            "human_approval_required": False,
        }
        self._save_item(content_id)

    def update_state(self, content_id: str, next_state: ContentState):
        item = self.items.get(content_id)
        if not item:
            raise ValueError("Item not found")

        StateMachine.validate_transition(item["state"], next_state)

        # Governance check
        if next_state == ContentState.READY:
            platform = item["data"].get("platform")
            if platform in self.config.get("publishing", {}).get("governance", {}).get("require_human_approval_for", []):
                item["human_approval_required"] = True

        item["state"] = next_state
        item["history"].append(next_state)
        self._save_item(content_id)

    def get_ready_items(self, platform: str) -> List[Dict]:
        return [
            item
            for item in self.items.values()
            if item["state"] == ContentState.READY
            and item["data"].get("platform") == platform
            and not item["human_approval_required"]
        ]

    def approve(self, content_id: str):
        if content_id in self.items:
            self.items[content_id]["human_approval_required"] = False
            self._save_item(content_id)
