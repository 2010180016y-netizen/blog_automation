import unittest
import os
import json
from app.track.link_builder import LinkBuilder
from app.track.event_collector import EventCollector
from app.track.metrics import MetricsAggregator

class TestTracking(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_tracking.db"
        self.collector = EventCollector(self.db_path)
        self.aggregator = MetricsAggregator(self.db_path)
        self.builder = LinkBuilder({})

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_link_builder(self):
        url = "https://smartstore.naver.com/test"
        link = self.builder.build_tracking_link(url, "naver", "post1", "sku1", "buy")
        self.assertIn("ch=naver", link)
        self.assertIn("cid=post1", link)
        self.assertIn("sku=sku1", link)
        self.assertIn("intent=buy", link)

    def test_event_collection_and_metrics(self):
        # Collect some events
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("cta_click", "naver", "p1", "s1", "info")
        self.collector.collect("copy_coupon", "naver", "p1", "s1", "info")

        summary = self.aggregator.get_summary_by_content()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["views"], 2)
        self.assertEqual(summary[0]["clicks"], 1)
        self.assertEqual(summary[0]["conversions"], 1)
        self.assertEqual(summary[0]["ctr"], 50.0)
        self.assertEqual(summary[0]["cvr"], 50.0)

    def test_rejects_unsupported_filter_columns(self):
        with self.assertRaises(ValueError):
            self.collector.get_events({"drop table events;--": "x"})

    def test_metadata_sanitization_masks_and_drops_pii(self):
        self.collector.collect(
            "page_view", "naver", "p2", "s2", "info",
            {
                "email": "user@example.com",
                "profile": {
                    "phone": "010-1234-5678",
                    "note": "contact me at test@example.com"
                },
                "campaign": "spring"
            }
        )

        events = self.collector.get_events({"content_id": "p2"})
        self.assertEqual(len(events), 1)
        metadata = events[0]["metadata"]
        self.assertIn("[redacted_email]", metadata)
        self.assertNotIn("010-1234-5678", metadata)
        self.assertNotIn('"email"', metadata)
        self.assertNotIn('"phone"', metadata)

    def test_purge_old_events(self):
        self.collector.collect("page_view", "naver", "p3", "s3", "info", {"campaign": "old"})

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE events SET timestamp = '2000-01-01 00:00:00' WHERE content_id = ?", ("p3",))

        deleted = self.collector.purge_old_events(retention_days=30)
        self.assertGreaterEqual(deleted, 1)
        events = self.collector.get_events({"content_id": "p3"})
        self.assertEqual(len(events), 0)

    def test_pii_drop_logs_are_structured_json(self):
        with self.assertLogs("content_os.audit", level="WARNING") as cm:
            self.collector.collect(
                "page_view", "naver", "p4", "s4", "info",
                {"email": "user@example.com", "profile": {"phone": "010-1234-5678"}, "safe": "ok"}
            )

        self.assertGreaterEqual(len(cm.output), 1)
        raw = cm.output[0].split("WARNING:content_os.audit:", 1)[-1]
        payload = json.loads(raw)
        self.assertEqual(payload["event"], "PII_METADATA_KEYS_DROPPED")
        self.assertEqual(payload["content_id"], "p4")
        self.assertIn("email", payload["dropped_keys"][0])

if __name__ == "__main__":
    unittest.main()
