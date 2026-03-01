import os
import sqlite3
import tempfile
import unittest

from app.store.affiliate_import import (
    AffiliateImportRepository,
    import_affiliate_csv,
    parse_affiliate_csv,
)


class TestAffiliateImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.tmp.name, "links.csv")
        self.db_path = os.path.join(self.tmp.name, "aff.db")

    def tearDown(self):
        self.tmp.cleanup()

    def write_csv(self, body: str):
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write(body)

    def read_count(self, table: str) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()

    def test_parse_basic(self):
        self.write_csv("sku,product_name,affiliate_url,price\nS1,P1,https://a.com/p1,1000\n")
        rows, errs = parse_affiliate_csv(self.csv_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].sku, "S1")
        self.assertEqual(rows[0].price, 1000)
        self.assertEqual(errs, [])

    def test_parse_header_aliases(self):
        self.write_csv("product_sku,title,link\nS1,T1,https://a.com/x\n")
        rows, errs = parse_affiliate_csv(self.csv_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].product_name, "T1")
        self.assertEqual(errs, [])

    def test_parse_invalid_url_error(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,not-url\n")
        rows, errs = parse_affiliate_csv(self.csv_path)
        self.assertEqual(len(rows), 0)
        self.assertEqual(errs[0]["error"], "invalid_url")

    def test_parse_missing_field_error(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,,https://a.com\n")
        rows, errs = parse_affiliate_csv(self.csv_path)
        self.assertEqual(len(rows), 0)
        self.assertEqual(errs[0]["error"], "missing_required_field")

    def test_parse_dedup_by_sku_url(self):
        self.write_csv(
            "sku,product_name,affiliate_url\n"
            "S1,P1,https://a.com/x\n"
            "S1,P1dup,https://a.com/x\n"
        )
        rows, errs = parse_affiliate_csv(self.csv_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(errs, [])

    def test_upsert_products_source_type_affiliate(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/x\n")
        result = import_affiliate_csv(self.csv_path, db_path=self.db_path)
        self.assertEqual(result["upserted"], 1)

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT source_type, disclosure_required FROM products WHERE sku='S1'").fetchone()
            self.assertEqual(row[0], "AFFILIATE_SC")
            self.assertEqual(row[1], 1)
        finally:
            conn.close()

    def test_queue_generates_multiple_intents(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/x\n")
        result = import_affiliate_csv(self.csv_path, db_path=self.db_path, intents=["info", "compare"])
        self.assertGreaterEqual(result["queued"], 2)

        conn = sqlite3.connect(self.db_path)
        try:
            intents = [r[0] for r in conn.execute("SELECT intent FROM content_queue WHERE sku='S1'").fetchall()]
            self.assertIn("info", intents)
            self.assertIn("compare", intents)
        finally:
            conn.close()

    def test_queue_dedup_on_repeat_import(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/x\n")
        import_affiliate_csv(self.csv_path, db_path=self.db_path, intents=["info", "compare"])
        import_affiliate_csv(self.csv_path, db_path=self.db_path, intents=["info", "compare"])
        self.assertEqual(self.read_count("content_queue"), 2)

    def test_invalid_intent_fallback(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/x\n")
        import_affiliate_csv(self.csv_path, db_path=self.db_path, intents=["bad-intent"])
        conn = sqlite3.connect(self.db_path)
        try:
            intents = sorted(r[0] for r in conn.execute("SELECT intent FROM content_queue").fetchall())
            self.assertEqual(intents, ["compare", "info"])
        finally:
            conn.close()

    def test_upsert_overwrites_url(self):
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/x\n")
        import_affiliate_csv(self.csv_path, db_path=self.db_path)
        self.write_csv("sku,product_name,affiliate_url\nS1,P1,https://a.com/y\n")
        import_affiliate_csv(self.csv_path, db_path=self.db_path)

        conn = sqlite3.connect(self.db_path)
        try:
            url = conn.execute("SELECT affiliate_url FROM products WHERE sku='S1'").fetchone()[0]
            self.assertEqual(url, "https://a.com/y")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
