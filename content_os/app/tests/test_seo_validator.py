import unittest
from app.seo.validator import SEOValidator

class TestSEOValidator(unittest.TestCase):
    def setUp(self):
        self.config = {
            "qa": {
                "unique_pack": ["faq", "table"]
            }
        }
        self.validator = SEOValidator(self.config)

    def test_technical_seo_validation(self):
        html = """
        <html>
            <head>
                <link rel="canonical" href="https://example.com">
                <meta name="description" content="test">
                <meta property="og:title" content="test">
                <script type="application/ld+json">{}</script>
            </head>
        </html>
        """
        report = self.validator.validate_technical_seo(html)
        self.assertTrue(report["valid"])

    def test_technical_seo_missing(self):
        html = "<html><head></head></html>"
        report = self.validator.validate_technical_seo(html)
        self.assertFalse(report["valid"])
        self.assertIn("canonical", report["missing"])

    def test_unique_pack_validation(self):
        content_data = {
            "faq": [{"q": "a"}],
            "table": {"headers": [], "rows": []}
        }
        report = self.validator.validate_unique_pack(content_data)
        self.assertTrue(report["valid"])
        self.assertIn("faq", report["found"])

    def test_unique_pack_insufficient(self):
        content_data = {"faq": []}
        report = self.validator.validate_unique_pack(content_data)
        self.assertFalse(report["valid"])

if __name__ == "__main__":
    unittest.main()
