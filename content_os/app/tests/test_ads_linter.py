import unittest
from app.ads.linter import AdsLinter

class TestAdsLinter(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ads_ux": {
                "rules": {
                    "min_distance_from_cta_px": 120,
                    "forbid_near_elements": ["button", "input"]
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
            <button class="cta-button">Buy Now</button>
        </div>
        """
        # In this case, there's a <p> between ad and button, so it might pass our simple sibling check
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "PASS")

    def test_violation_html(self):
        html = """
        <div>
            <div class="ad-unit">Ad Content</div>
            <button>Click Me</button>
        </div>
        """
        # Ad and button are immediate siblings
        report = self.linter.lint(html)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(len(report["violations"]) > 0)
        self.assertIn("immediately adjacent", report["violations"][0]["message"])

if __name__ == "__main__":
    unittest.main()
