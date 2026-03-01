import json
import os
import tempfile
import unittest

from app.publish.content_queue_state import ContentQueueService, QueueState
from app.refresh.content_refresh import ContentRefreshService, RefreshEvent


class TestContentRefreshSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "refresh.db")
        self.out_dir = os.path.join(self.tmpdir.name, "out", "update_packs")

        self.queue = ContentQueueService(db_path=self.db_path)
        self.refresh = ContentRefreshService(db_path=self.db_path, out_dir=self.out_dir)

        self.published_item = self.queue.create_item(
            sku="SKU-1",
            intent="review",
            source_type="MY_STORE",
            payload={"product_id": "PID-1", "title": "테스트 상품"},
        )
        self.queue.transition(self.published_item, QueueState.QA_PASS)
        self.queue.transition(self.published_item, QueueState.READY)
        self.queue.transition(self.published_item, QueueState.PUBLISHED)

        self.draft_item = self.queue.create_item(
            sku="SKU-1",
            intent="info",
            source_type="MY_STORE",
            payload={"product_id": "PID-1"},
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_detect_my_store_field_changes(self):
        changes = self.refresh.detect_changes(
            before={"price": 10000, "options": ["A"], "shipping": "무료", "status": "ON"},
            after={"price": 9000, "options": ["A", "B"], "shipping": "유료", "status": "OFF"},
        )
        fields = {c["field"] for c in changes}
        self.assertEqual(fields, {"price", "options", "shipping", "status"})

    def test_detect_faq_added_trigger(self):
        changes = self.refresh.detect_changes(
            before={"faq": ["기존 질문"]},
            after={"faq": ["기존 질문", "새 질문"]},
        )
        self.assertIn("faq_added", {c["field"] for c in changes})

    def test_detect_cs_changed_trigger(self):
        changes = self.refresh.detect_changes(
            before={"cs": "평균 24시간 응대"},
            after={"cs": "평균 12시간 응대"},
        )
        self.assertIn("cs", {c["field"] for c in changes})

    def test_find_impacted_content_only_published(self):
        impacted = self.refresh.find_impacted_content(product_id="PID-1", sku="SKU-1")
        self.assertEqual(len(impacted), 1)
        self.assertEqual(impacted[0]["content_id"], str(self.published_item))

    def test_build_update_pack_contains_locations_and_change_log(self):
        event = RefreshEvent(
            product_id="PID-1",
            sku="SKU-1",
            before={"price": 10000},
            after={"price": 9000},
        )
        changes = self.refresh.detect_changes(event.before, event.after)
        content = self.refresh.find_impacted_content(product_id="PID-1", sku="SKU-1")[0]

        pack = self.refresh.build_update_pack(content=content, event=event, changes=changes)

        self.assertEqual(pack["content_id"], str(self.published_item))
        self.assertEqual(pack["update_pack"][0]["target"]["section"], "가격/혜택")
        self.assertEqual(pack["update_pack"][0]["target"]["paragraph"], 2)
        self.assertGreaterEqual(len(pack["change_log"]), 1)

    def test_process_event_writes_update_pack_file(self):
        event = RefreshEvent(
            product_id="PID-1",
            sku="SKU-1",
            before={"price": 10000, "faq": ["q1"], "cs": "24h"},
            after={"price": 9500, "faq": ["q1", "q2"], "cs": "12h"},
        )
        paths = self.refresh.process_event(event)

        self.assertEqual(len(paths), 1)
        self.assertTrue(os.path.exists(paths[0]))

        with open(paths[0], "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["content_id"], str(self.published_item))
        self.assertIn("price", payload["trigger"])
        self.assertIn("faq_added", payload["trigger"])
        self.assertIn("cs", payload["trigger"])

    def test_process_event_returns_empty_when_no_change(self):
        event = RefreshEvent(
            product_id="PID-1",
            sku="SKU-1",
            before={"price": 10000, "status": "ON"},
            after={"price": 10000, "status": "ON"},
        )
        paths = self.refresh.process_event(event)
        self.assertEqual(paths, [])


if __name__ == "__main__":
    unittest.main()
