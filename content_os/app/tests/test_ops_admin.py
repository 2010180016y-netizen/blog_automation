import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage.repo import ProductRepo
from app.store.unified_products import ensure_unified_products_table


class TestOpsAdmin(unittest.TestCase):
    def test_dashboard_and_product_planning_flow(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "blogs.db")
            repo = ProductRepo(db)
            ensure_unified_products_table(db)
            with sqlite3.connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO products (sku, source_type, name, price, shipping, product_link, options, as_info, mandatory_disclaimer, evidence_data)
                    VALUES (?, ?, ?, ?, ?, ?, '{}', '', '', '{}')
                    """,
                    ("SKU-1", "AFFILIATE_SHOPPING_CONNECT", "상품1", None, "", "https://example.com/p1"),
                )

            dash = client.get("/ops/dashboard")
            self.assertEqual(dash.status_code, 200)
            self.assertIn("상품 운영 대시보드", dash.text)

            update = client.post(
                "/ops/products/planning",
                json={
                    "sku": "SKU-1",
                    "priority": 90,
                    "excluded": False,
                    "preferred_intent": "review",
                    "db_path": db,
                },
            )
            self.assertEqual(update.status_code, 200)

            rows = client.get("/ops/products", params={"db_path": db}).json()
            self.assertEqual(rows[0]["sku"], "SKU-1")
            self.assertEqual(rows[0]["priority"], 90)

            candidates = client.get("/ops/content-candidates", params={"db_path": db}).json()
            self.assertEqual(candidates[0]["primary_intent"], "review")
            self.assertIn("template_map", candidates[0])


if __name__ == "__main__":
    unittest.main()
