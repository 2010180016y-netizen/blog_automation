import unittest

from app.ads.linter import AdsLinter


class TestAdsLinter(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ads_ux": {
                "rules": {
                    "min_distance_from_cta_px": 120,
                    "forbid_near_elements": ["button", "input", "select", "video"],
                }
            }
        }
        self.linter = AdsLinter(self.config)

    def test_clean_html(self):
        html = """
        <div>
            <h1>Title</h1>
            <p>Some content here...</p>
            <div class="ad-unit">Ad Content</div>
            <p>More content...</p>
            <p>Even more content...</p>
            <button class="cta-button">Buy Now</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "PASS")

    def test_violation_near_cta(self):
        html = """
        <div>
            <div class="ad-unit">Ad Content</div>
            <button>Click Me</button>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(len(report["violations"]) > 0)
        self.assertIn("too close", report["violations"][0]["message"])

    def test_violation_inside_interactive_container(self):
        html = """
        <div>
            <div class="ad-unit"><button>play</button></div>
        </div>
        """
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("contains an interactive control", report["violations"][0]["message"])


if __name__ == "__main__":
    unittest.main()
