import sqlite3
import tempfile
import unittest
from pathlib import Path

import httpx

from app.store.commerce_ssot import (
    CommerceAPIConfig,
    NaverCommerceAPIClient,
    ensure_ssot_table,
    upsert_ssot_rows,
)


class TestCommerceSSOT(unittest.TestCase):
    def test_fetch_ssot_rows(self):
        def fake_request(method, url, headers=None, json=None):
            if url.endswith('/v1/products/search'):
                data = {"contents": [{"channelProductNo": "1001", "originProductNo": "9001", "productUrl": "https://smartstore/p/1001"}]}
            elif '/v2/products/channel-products/1001' in url:
                data = {"name": "상품A", "salePrice": 19900, "deliveryInfo": {"baseFee": 0}, "productUrl": "https://smartstore/p/1001"}
            elif '/v2/products/origin-products/9001' in url:
                data = {"name": "원상품A"}
            else:
                raise AssertionError(url)
            req = httpx.Request(method, url)
            return httpx.Response(200, json=data, request=req)

        client = NaverCommerceAPIClient(
            CommerceAPIConfig(base_url="https://api.commerce.naver.com", token="t"),
            requester=fake_request,
        )
        rows = client.fetch_ssot_rows(page=1, size=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sku"], "1001")
        self.assertEqual(rows[0]["name"], "상품A")
        self.assertEqual(rows[0]["price"], 19900)

    def test_upsert_ssot_rows(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / 'blogs.db'
            ensure_ssot_table(str(db))
            res = upsert_ssot_rows(
                str(db),
                [
                    {
                        "sku": "1001",
                        "channel_product_no": "1001",
                        "origin_product_no": "9001",
                        "name": "상품A",
                        "price": 10000,
                        "shipping": "0",
                        "product_link": "https://smartstore/p/1001",
                        "raw_search": "{}",
                        "raw_channel": "{}",
                        "raw_origin": "{}",
                    }
                ],
            )
            self.assertEqual(res["upserted"], 1)
            with sqlite3.connect(db) as conn:
                cnt = conn.execute("SELECT COUNT(*) FROM products_ssot").fetchone()[0]
                self.assertEqual(cnt, 1)


if __name__ == '__main__':
    unittest.main()
