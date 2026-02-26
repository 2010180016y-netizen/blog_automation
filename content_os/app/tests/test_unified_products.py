import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.store.unified_products import (
    AFFILIATE_PRICE_NOTE_KO,
    SOURCE_AFFILIATE,
    SOURCE_MY_STORE,
    ensure_unified_products_table,
    sync_unified_products,
)


class TestUnifiedProducts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "blogs.db"

        with sqlite3.connect(self.db) as conn:
            conn.execute(
                """
                CREATE TABLE products_ssot (
                    sku TEXT PRIMARY KEY,
                    channel_product_no TEXT,
                    origin_product_no TEXT,
                    name TEXT,
                    price INTEGER,
                    shipping TEXT,
                    product_link TEXT,
                    raw_search TEXT,
                    raw_channel TEXT,
                    raw_origin TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE partner_products (
                    partner_product_id TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    category TEXT,
                    affiliate_link TEXT,
                    advertiser TEXT,
                    commission_note TEXT,
                    usage_mode TEXT,
                    raw_payload TEXT,
                    updated_at TEXT
                )
                """
            )

            conn.execute(
                "INSERT INTO products_ssot VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "OWN001",
                    "OWN001",
                    "OR001",
                    "내상품",
                    10000,
                    "0",
                    "https://smartstore/p/own001",
                    "{}",
                    "{}",
                    "{}",
                    "2026-01-01",
                ),
            )
            conn.execute(
                "INSERT INTO partner_products VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    "PT001",
                    "shopping_connect",
                    "제휴상품",
                    "테스트",
                    "https://shoppingconnect.link/abc",
                    "네이버플러스",
                    None,
                    "commercial",
                    "{}",
                    "2026-01-01",
                ),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def test_sync_and_source_type(self):
        out = Path(self.tmp.name) / "refresh.json"
        result = sync_unified_products(str(self.db), refresh_queue_path=str(out))
        self.assertEqual(result["upserted"], 2)

        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT sku, source_type, mandatory_disclaimer FROM products ORDER BY sku").fetchall()
            self.assertEqual(len(rows), 2)
            row_map = {r["sku"]: dict(r) for r in rows}
            self.assertEqual(row_map["OWN001"]["source_type"], SOURCE_MY_STORE)
            self.assertEqual(row_map["PT001"]["source_type"], SOURCE_AFFILIATE)
            self.assertEqual(row_map["PT001"]["mandatory_disclaimer"], AFFILIATE_PRICE_NOTE_KO)

        self.assertTrue(out.exists())

    def test_my_store_change_creates_refresh_candidate(self):
        ensure_unified_products_table(str(self.db))
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "INSERT INTO products(sku,source_type,name,price,shipping,product_link,options,as_info,mandatory_disclaimer,evidence_data) VALUES(?,?,?,?,?,?,?,?,?,?)",
                ("OWN001", SOURCE_MY_STORE, "내상품", 9000, "0", "https://smartstore/p/own001", "{}", "", "", "{}"),
            )

        result = sync_unified_products(str(self.db))
        self.assertIn("OWN001", result["refresh_queue"]["skus"])


if __name__ == "__main__":
    unittest.main()
