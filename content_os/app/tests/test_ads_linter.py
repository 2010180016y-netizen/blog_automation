import unittest

from app.ads.linter import AdsLinter


class TestAdsLinter(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ads_ux": {
                "rules": {
                    "min_distance_from_cta_px": 120,
                    "forbid_near_elements": ["button", "input"],
                    "reject_if_gap_nodes_le": 0,
                    "warn_if_gap_nodes_le": 2,
                }
            }
        }
        self.linter = AdsLinter(self.config)

    def test_clean_html_pass(self):
        html = """
        <div>
            <h1>Title</h1>
            <div class="ad-unit">Ad Content</div>
            <p>content 1</p>
            <p>content 2</p>
            <p>content 3</p>
            <button class="cta-button">Buy Now</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["summary"]["reject_count"], 0)
        self.assertEqual(report["summary"]["warn_count"], 0)

    def test_reject_when_immediately_adjacent(self):
        html = """
        <div>
            <div class="ad-unit">Ad</div>
            <button>Click</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(v["level"] == "REJECT" for v in report["violations"]))

    def test_warn_when_one_gap_node(self):
        html = """
        <div>
            <div class="ad-unit">Ad</div>
            <p>spacer</p>
            <button>Click</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "WARN")
        self.assertTrue(any(v["level"] == "WARN" for v in report["violations"]))

    def test_warn_when_two_gap_nodes(self):
        html = """
        <div>
            <div class="ad-unit">Ad</div>
            <p>spacer1</p>
            <p>spacer2</p>
            <input />
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "WARN")

    def test_ignores_elements_in_different_parent(self):
        html = """
        <section>
            <div class="ad-unit">Ad</div>
        </section>
        <section>
            <button>Click</button>
        </section>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "PASS")

    def test_detects_ins_adsbygoogle_selector(self):
        html = """
        <div>
            <ins class="adsbygoogle">Ad</ins>
            <button>CTA</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "REJECT")

    def test_empty_html_passes(self):
        report = self.linter.lint("   ")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["summary"]["checked_ad_units"], 0)

    def test_violation_contains_debug_fields(self):
        html = """
        <div>
            <div id="ad1" class="ad-unit">Ad</div>
            <button id="buy">Buy</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "REJECT")
        v = report["violations"][0]
        self.assertIn("gap_nodes", v)
        self.assertIn("rule", v)
        self.assertIn("offending_element", v)


if __name__ == "__main__":
    unittest.main()
