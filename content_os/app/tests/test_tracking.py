import unittest
import os
import shutil
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

if __name__ == "__main__":
    unittest.main()
