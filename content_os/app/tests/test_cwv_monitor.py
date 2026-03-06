import unittest

from app.seo.cwv_monitor import (
    build_cwv_alert_report,
    default_performance_budgets,
    detect_regressions,
    evaluate_cwv_by_page_type,
)


class TestCWVMonitor(unittest.TestCase):
    def test_budget_evaluation(self):
        rows = [
            {"page": "/landing-a", "page_type": "landing", "lcp": 2.1, "inp": 150, "cls": 0.04, "ttfb": 0.5},
            {"page": "/review-a", "page_type": "review", "lcp": 3.2, "inp": 280, "cls": 0.14, "ttfb": 1.1},
        ]
        report = evaluate_cwv_by_page_type(rows, budgets=default_performance_budgets())
        self.assertEqual(report["overall"], "FAIL")
        self.assertEqual(report["findings"][0]["severity"], "PASS")
        self.assertIn(report["findings"][1]["severity"], ["WARN", "FAIL"])

    def test_regression_detection(self):
        curr = [{"page": "/p1", "page_type": "landing", "lcp": 2.8, "inp": 240, "cls": 0.11, "ttfb": 0.95}]
        prev = [{"page": "/p1", "page_type": "landing", "lcp": 2.3, "inp": 180, "cls": 0.07, "ttfb": 0.75}]
        regressions = detect_regressions(curr, prev)
        self.assertEqual(len(regressions), 1)
        self.assertTrue(any(r["metric"] == "lcp" for r in regressions[0]["regressions"]))

    def test_alert_cause_breakdown(self):
        curr = [
            {
                "page": "/cmp-phone",
                "page_type": "comparison",
                "lcp": 3.4,
                "inp": 310,
                "cls": 0.13,
                "ttfb": 1.2,
                "image_kb": 1200,
                "ad_script_kb": 310,
                "plugin_script_kb": 350,
            }
        ]
        prev = [{"page": "/cmp-phone", "page_type": "comparison", "lcp": 2.7, "inp": 220, "cls": 0.08, "ttfb": 0.9}]
        report = build_cwv_alert_report(curr, prev)
        self.assertIn(report["overall"], ["WARN", "FAIL"])
        self.assertEqual(len(report["alerts"]), 1)
        causes = report["alerts"][0]["probable_causes"]
        components = {c["component"] for c in causes}
        self.assertIn("image", components)
        self.assertIn("ad_script", components)


if __name__ == "__main__":
    unittest.main()
