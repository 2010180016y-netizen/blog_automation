import tempfile
import unittest
from pathlib import Path

from app.store.shopping_connect_ingest import (
    load_rows_from_csv,
    normalize_rows,
    validate_shopping_connect_rows,
)


class TestShoppingConnectIngest(unittest.TestCase):
    def test_csv_normalize_and_validate(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "partner.csv"
            p.write_text(
                "partner_product_id,title,affiliate_link,category,keywords,content_type,source,usage_mode\n"
                "PT001,테스트상품,https://shoppingconnect.link/a,가전,공기청정기|필터,review,shopping_connect,commercial\n",
                encoding="utf-8",
            )
            rows = load_rows_from_csv(str(p))
            normalized = normalize_rows(rows)
            report = validate_shopping_connect_rows(normalized)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(normalized[0]["content_type"], "review")

    def test_policy_reject_wrong_source(self):
        rows = normalize_rows(
            [
                {
                    "partner_product_id": "PTX",
                    "title": "x",
                    "affiliate_link": "https://example.com",
                    "source": "shopping_search_api",
                    "usage_mode": "commercial",
                    "content_type": "review",
                }
            ]
        )
        report = validate_shopping_connect_rows(rows)
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
