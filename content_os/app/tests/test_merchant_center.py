import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.seo.merchant_center import (
    detect_product_changes,
    generate_merchant_center_feed,
    generate_product_merchant_jsonld,
    load_products_from_db,
    validate_merchant_item,
)


class TestMerchantCenter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "blogs.db"

        with sqlite3.connect(self.db) as conn:
            conn.execute(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT,
                    name TEXT,
                    price INTEGER,
                    shipping TEXT,
                    product_link TEXT,
                    options TEXT,
                    as_info TEXT,
                    prohibited_expressions TEXT,
                    mandatory_disclaimer TEXT,
                    evidence_data TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO products(sku,name,price,shipping,product_link,options,as_info,mandatory_disclaimer,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                ("SKU001", "상품A", 19900, "무료배송", "https://example.com/p/sku001", "{}", "설명", "고지", "2026-01-01"),
            )
            conn.execute(
                "INSERT INTO products(sku,name,price,shipping,product_link,options,as_info,mandatory_disclaimer,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                ("SKU002", "상품B", 0, "3000", "https://example.com/p/sku002", "{}", "설명", "고지", "2026-01-02"),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_products(self):
        products = load_products_from_db(str(self.db))
        self.assertEqual(len(products), 2)

    def test_jsonld_generation(self):
        products = load_products_from_db(str(self.db))
        jsonld = generate_product_merchant_jsonld(products[0], site_url="https://example.com")
        self.assertEqual(jsonld["@type"], "Product")
        self.assertEqual(jsonld["offers"]["priceCurrency"], "KRW")

    def test_validation(self):
        errors = validate_merchant_item({"sku": "S", "name": "N", "price": 0, "product_link": "https://e.com"})
        self.assertIn("price must be greater than 0", errors)

    def test_feed_generation_with_validation(self):
        products = load_products_from_db(str(self.db))
        out = Path(self.tmp.name) / "merchant.xml"
        report = generate_merchant_center_feed(products, str(out), "https://example.com")
        self.assertEqual(report["valid_count"], 1)
        self.assertEqual(report["error_count"], 1)
        self.assertTrue(out.exists())

    def test_change_detection(self):
        products = load_products_from_db(str(self.db))
        snapshot = Path(self.tmp.name) / "snapshot.json"

        first = detect_product_changes(products, str(snapshot))
        self.assertEqual(first["new"], ["SKU001", "SKU002"])

        # mutate one product
        products[0]["price"] = 29900
        second = detect_product_changes(products, str(snapshot))
        self.assertIn("SKU001", second["changed"])


if __name__ == "__main__":
    unittest.main()
