import unittest

from app.pipeline.image_seo import (
    apply_lazy_loading_to_html,
    detect_keyword_stuffing_alt,
    generate_descriptive_alt_text,
)


class TestImageSEO(unittest.TestCase):
    def test_lazy_loading_injection(self):
        html = '<div><img src="/a.jpg" alt="sample"></div>'
        out = apply_lazy_loading_to_html(html)
        self.assertIn('loading="lazy"', out)
        self.assertIn('decoding="async"', out)

    def test_alt_text_description_first(self):
        alt = generate_descriptive_alt_text(
            image_path="/tmp/air-purifier-front-view.jpg",
            sku="SKU001",
            context="living room setup",
            primary_keyword="best air purifier",
        )
        self.assertIn("SKU001", alt)
        self.assertIn("living room setup", alt)

    def test_keyword_stuffing_detection(self):
        bad = "air purifier air purifier air purifier air purifier"
        self.assertTrue(detect_keyword_stuffing_alt(bad, ["air purifier"], max_keyword_repeats=1))


if __name__ == "__main__":
    unittest.main()
