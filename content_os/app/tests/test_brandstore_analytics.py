import unittest

from app.store.brandstore_analytics import summarize_brandstore_stats


class TestBrandstoreAnalytics(unittest.TestCase):
    def test_summary(self):
        rows = [
            {"page_type": "landing", "impressions": 1000, "clicks": 100, "orders": 5, "revenue": 100000},
            {"page_type": "review", "impressions": 500, "clicks": 40, "orders": 3, "revenue": 55000},
        ]
        s = summarize_brandstore_stats(rows)
        self.assertEqual(s["totals"]["impressions"], 1500)
        self.assertEqual(s["totals"]["orders"], 8)
        self.assertIn("landing", s["by_page_type"])


if __name__ == "__main__":
    unittest.main()
