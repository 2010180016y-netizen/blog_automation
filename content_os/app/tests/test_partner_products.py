import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.store.commerce_ssot import ensure_ssot_table, upsert_ssot_rows
from app.store.partner_products import (
    build_two_track_ssot,
    export_two_track_ssot,
    upsert_partner_products,
    validate_partner_product_source,
)


class TestPartnerProducts(unittest.TestCase):
    def test_policy_reject_for_shopping_search_commercial(self):
        report = validate_partner_product_source(
            [
                {
                    "id": "x1",
                    "source": "shopping_search_api",
                    "affiliate_link": "https://example.com",
                    "usage_mode": "commercial",
                }
            ]
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(report["violations"])

    def test_two_track_merge(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "blogs.db"

            ensure_ssot_table(str(db))
            upsert_ssot_rows(
                str(db),
                [
                    {
                        "sku": "OWN001",
                        "channel_product_no": "OWN001",
                        "origin_product_no": "OR001",
                        "name": "내상품",
                        "price": 12000,
                        "shipping": "0",
                        "product_link": "https://smartstore/p/own001",
                        "raw_search": "{}",
                        "raw_channel": "{}",
                        "raw_origin": "{}",
                    }
                ],
            )

            sync = upsert_partner_products(
                str(db),
                [
                    {
                        "partner_product_id": "PT001",
                        "source": "shopping_connect",
                        "title": "제휴상품",
                        "affiliate_link": "https://shoppingconnect.link/abc",
                        "usage_mode": "commercial",
                    }
                ],
            )
            self.assertEqual(sync["upserted"], 1)

            merged = build_two_track_ssot(str(db))
            tracks = {r["track"] for r in merged}
            self.assertIn("own_store", tracks)
            self.assertIn("partner_store", tracks)

            out = Path(td) / "merged.json"
            result = export_two_track_ssot(str(db), str(out))
            self.assertEqual(result["count"], 2)
            self.assertTrue(out.exists())

    def test_partner_upsert_rejected_does_not_insert(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "blogs.db"
            result = upsert_partner_products(
                str(db),
                [
                    {
                        "partner_product_id": "PTX",
                        "source": "naver_shopping_openapi",
                        "title": "위험소스",
                        "affiliate_link": "https://example",
                        "usage_mode": "commercial",
                    }
                ],
            )
            self.assertEqual(result["upserted"], 0)
            self.assertEqual(result["validation"]["status"], "REJECT")
            with sqlite3.connect(db) as conn:
                cnt = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='partner_products'").fetchone()[0]
                self.assertEqual(cnt, 0)


if __name__ == "__main__":
    unittest.main()
