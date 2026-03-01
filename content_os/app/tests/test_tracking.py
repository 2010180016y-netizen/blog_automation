import csv
import os
import tempfile
import unittest

from app.track.link_builder import LinkBuilder
from app.track.event_collector import EventCollector
from app.track.metrics import MetricsAggregator


class TestTracking(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test_tracking.db")
        self.collector = EventCollector(self.db_path)
        self.aggregator = MetricsAggregator(self.db_path)
        self.builder = LinkBuilder({})

    def tearDown(self):
        self.tmp.cleanup()

    def test_link_builder_includes_all_required_params(self):
        url = "https://smartstore.naver.com/test"
        link = self.builder.build_tracking_link(url, "naver", "post1", "sku1", "buy")
        self.assertIn("ch=naver", link)
        self.assertIn("cid=post1", link)
        self.assertIn("sku=sku1", link)
        self.assertIn("intent=buy", link)

    def test_link_builder_supports_variant_param(self):
        url = "https://smartstore.naver.com/test"
        link = self.builder.build_tracking_link(url, "naver", "post1", "sku1", "buy", variant="A")
        self.assertIn("variant=A", link)

    def test_link_builder_preserves_existing_query(self):
        url = "https://a.com/p?foo=1"
        link = self.builder.build_tracking_link(url, "chx", "c1", "s1", "info")
        self.assertIn("foo=1", link)
        self.assertIn("ch=chx", link)

    def test_link_builder_missing_param_raises(self):
        with self.assertRaises(ValueError):
            self.builder.build_tracking_link("https://a.com", "", "cid", "sku", "info")

    def test_link_builder_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            self.builder.build_tracking_link("not-url", "n", "cid", "sku", "info")

    def test_event_collect_valid_types(self):
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("cta_click", "naver", "p1", "s1", "info")
        self.collector.collect("store_click", "naver", "p1", "s1", "info")
        events = self.collector.get_events()
        self.assertEqual(len(events), 3)

    def test_event_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            self.collector.collect("copy_coupon", "naver", "p1", "s1", "info")

    def test_event_missing_required_field_raises(self):
        with self.assertRaises(ValueError):
            self.collector.collect("page_view", "", "p1", "s1", "info")

    def test_get_events_filter_allowlist(self):
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("page_view", "google", "p2", "s2", "info")
        rows = self.collector.get_events({"channel": "naver"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["channel"], "naver")

    def test_get_events_invalid_filter_raises(self):
        with self.assertRaises(ValueError):
            self.collector.get_events({"unknown": "x"})

    def test_metrics_ctr_cvr_accuracy(self):
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("cta_click", "naver", "p1", "s1", "info")
        self.collector.collect("store_click", "naver", "p1", "s1", "info")

        summary = self.aggregator.get_summary_by_content()
        self.assertEqual(len(summary), 1)
        row = summary[0]
        self.assertEqual(row["views"], 2)
        self.assertEqual(row["clicks"], 2)
        self.assertEqual(row["conversions"], 1)
        self.assertEqual(row["ctr"], 100.0)
        self.assertEqual(row["cvr"], 50.0)

    def test_metrics_group_by_cid_sku_intent(self):
        self.collector.collect("page_view", "naver", "p1", "s1", "info")
        self.collector.collect("page_view", "naver", "p1", "s1", "buy")
        self.collector.collect("page_view", "naver", "p2", "s2", "info")
        summary = self.aggregator.get_summary_by_content()
        self.assertEqual(len(summary), 3)

    def test_variant_ctr_and_winner(self):
        # Variant A
        self.collector.collect("page_view", "naver", "p-ab", "s1", "info", metadata={"variant": "A"})
        self.collector.collect("page_view", "naver", "p-ab", "s1", "info", metadata={"variant": "A"})
        self.collector.collect("cta_click", "naver", "p-ab", "s1", "info", metadata={"variant": "A"})
        # Variant B
        self.collector.collect("page_view", "naver", "p-ab", "s1", "info", metadata={"variant": "B"})
        self.collector.collect("page_view", "naver", "p-ab", "s1", "info", metadata={"variant": "B"})
        self.collector.collect("store_click", "naver", "p-ab", "s1", "info", metadata={"variant": "B"})
        self.collector.collect("cta_click", "naver", "p-ab", "s1", "info", metadata={"variant": "B"})

        rows = self.aggregator.get_variant_ctr("p-ab")
        self.assertEqual({r["variant"] for r in rows}, {"A", "B"})

        winner = self.aggregator.pick_winner_variant("p-ab")
        self.assertEqual(winner["winner"], "B")

    def test_export_metrics_csv_header(self):
        from scripts.export_metrics import export_metrics

        out_path = export_metrics(db_path=self.db_path)
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertEqual(header, ["content_id", "sku", "intent", "views", "clicks", "conversions", "ctr", "cvr"])


if __name__ == "__main__":
    unittest.main()
