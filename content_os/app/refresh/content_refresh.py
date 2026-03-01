import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RefreshEvent:
    product_id: str
    sku: Optional[str]
    before: Dict[str, Any]
    after: Dict[str, Any]


class ContentRefreshService:
    """Generate update packs for published content impacted by MY_STORE/FAQ/CS changes."""

    FIELD_SECTION_MAP = {
        "price": {"section": "가격/혜택", "paragraph": 2},
        "options": {"section": "옵션 안내", "paragraph": 3},
        "shipping": {"section": "배송/교환", "paragraph": 1},
        "status": {"section": "구매 가능 상태", "paragraph": 1},
        "faq_added": {"section": "FAQ", "paragraph": 1},
        "cs": {"section": "FAQ", "paragraph": 2},
    }

    def __init__(self, db_path: str = "blogs.db", out_dir: str = "out/update_packs"):
        self.db_path = db_path
        self.out_dir = out_dir

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def detect_changes(before: Dict[str, Any], after: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []

        tracked_fields = ("price", "options", "shipping", "status")
        for field in tracked_fields:
            old_v = before.get(field)
            new_v = after.get(field)
            if old_v != new_v:
                changes.append({"field": field, "old": old_v, "new": new_v})

        old_faq = before.get("faq") or []
        new_faq = after.get("faq") or []
        if len(new_faq) > len(old_faq):
            added = [q for q in new_faq if q not in old_faq]
            changes.append({"field": "faq_added", "old": old_faq, "new": added or new_faq})

        old_cs = before.get("cs")
        new_cs = after.get("cs")
        if old_cs != new_cs:
            changes.append({"field": "cs", "old": old_cs, "new": new_cs})

        return changes

    def find_impacted_content(self, product_id: str, sku: Optional[str] = None) -> List[Dict[str, Any]]:
        impacted: List[Dict[str, Any]] = []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, sku, intent, status, payload FROM content_queue WHERE status = 'PUBLISHED'"
            ).fetchall()

        for row in rows:
            payload = {}
            if row["payload"]:
                try:
                    payload = json.loads(row["payload"])
                except json.JSONDecodeError:
                    payload = {}

            queue_product_id = payload.get("product_id")
            if str(queue_product_id) == str(product_id) or (sku and str(row["sku"]) == str(sku)):
                impacted.append(
                    {
                        "content_id": str(row["id"]),
                        "sku": row["sku"],
                        "intent": row["intent"],
                        "payload": payload,
                    }
                )
        return impacted

    def build_update_pack(self, content: Dict[str, Any], event: RefreshEvent, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        updates = []
        change_log = []

        for idx, ch in enumerate(changes, start=1):
            field = ch["field"]
            loc = self.FIELD_SECTION_MAP.get(field, {"section": "본문", "paragraph": 1})
            updates.append(
                {
                    "target": {
                        "section": loc["section"],
                        "paragraph": loc["paragraph"],
                    },
                    "field": field,
                    "new_data": ch["new"],
                    "old_data": ch["old"],
                }
            )
            change_log.append(
                {
                    "order": idx,
                    "field": field,
                    "message": f"{field} 변경 감지",
                    "old": ch["old"],
                    "new": ch["new"],
                    "detected_at": now,
                }
            )

        return {
            "content_id": content["content_id"],
            "product_id": event.product_id,
            "sku": content["sku"],
            "intent": content["intent"],
            "trigger": [c["field"] for c in changes],
            "generated_at": now,
            "update_pack": updates,
            "change_log": change_log,
        }

    def write_update_pack(self, pack: Dict[str, Any]) -> str:
        os.makedirs(self.out_dir, exist_ok=True)
        path = os.path.join(self.out_dir, f"{pack['content_id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pack, f, ensure_ascii=False, indent=2)
        return path

    def process_event(self, event: RefreshEvent) -> List[str]:
        changes = self.detect_changes(event.before, event.after)
        if not changes:
            return []

        impacted = self.find_impacted_content(product_id=event.product_id, sku=event.sku)
        paths = []
        for content in impacted:
            pack = self.build_update_pack(content=content, event=event, changes=changes)
            paths.append(self.write_update_pack(pack))
        return paths
