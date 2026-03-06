import unittest

from app.seo.ops_dashboard import (
    detect_low_ctr_keywords,
    detect_indexing_error_increase,
    flag_high_rank_low_conversion,
    build_refresh_priority,
    generate_ops_dashboard,
)


class TestOpsDashboard(unittest.TestCase):
    def setUp(self):
        self.query_rows = [
            {"keyword": "갱년기 영양제", "impressions": 2000, "clicks": 20, "ctr": 0.01, "page": "/p1"},
            {"keyword": "콜라겐 추천", "impressions": 100, "clicks": 10, "ctr": 0.1, "page": "/p2"},
        ]
        self.page_rows = [
            {"content_id": "1", "page": "/p1", "impressions": 5000, "clicks": 200, "avg_position": 3.2, "ctr": 0.04},
            {"content_id": "2", "page": "/p2", "impressions": 700, "clicks": 20, "avg_position": 11.2, "ctr": 0.028},
        ]
        self.conversion_rows = [
            {"content_id": "1", "conversions": 0},
            {"content_id": "2", "conversions": 3},
        ]

    def test_low_ctr_keyword_detection(self):
        findings = detect_low_ctr_keywords(self.query_rows, min_impressions=300, ctr_threshold=0.02)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["keyword"], "갱년기 영양제")
        self.assertEqual(findings[0]["action"], "TITLE_META_AB_TEST")
        self.assertTrue(len(findings[0]["title_candidates"]) >= 2)

    def test_indexing_error_increase(self):
        current = {"google": {"errors": 8}, "naver": {"errors": 1}}
        previous = {"google": {"errors": 2}, "naver": {"errors": 1}}
        alerts = detect_indexing_error_increase(current, previous)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["source"], "google")
        self.assertEqual(alerts[0]["severity"], "HIGH")

    def test_high_rank_low_conversion_flag(self):
        flagged = flag_high_rank_low_conversion(self.page_rows, self.conversion_rows)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["content_id"], "1")
        self.assertEqual(flagged[0]["action"], "REVIEW_CTA_AND_PRODUCT_MATCH")

    def test_refresh_priority_ordering(self):
        ranking = build_refresh_priority(self.page_rows, self.conversion_rows)
        self.assertEqual(ranking[0]["content_id"], "1")

    def test_generate_dashboard(self):
        report = generate_ops_dashboard(
            query_rows=self.query_rows,
            page_rows=self.page_rows,
            conversion_rows=self.conversion_rows,
            current_index_status={"google": {"errors": 3}, "naver": {"errors": 0}},
            previous_index_status={"google": {"errors": 0}, "naver": {"errors": 0}},
        )
        self.assertIn(report["overall"], ["WARN", "FAIL"])
        self.assertTrue(len(report["low_ctr_keywords"]) >= 1)


if __name__ == "__main__":
    unittest.main()
