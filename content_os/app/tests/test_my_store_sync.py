import sqlite3
import time
import tempfile
import unittest
from pathlib import Path

import httpx

from app.ingest.naver_commerce.client import NaverCommerceClient
from app.ingest.naver_commerce.products import fetch_enriched_products
from app.ingest.naver_commerce.sync import sync_my_store_products
from app.storage.repo import ProductRepo


class FakeRequester:
    def __init__(self):
        self.calls = []
        self.fail_429_once = False
        self.fail_401_once = False

    def __call__(self, method, url, headers=None, json=None, data=None):
        self.calls.append((method, url, headers or {}, json or {}, data or {}))

        req = httpx.Request(method, url)
        if url.endswith('/v1/oauth2/token'):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 10800}, request=req)

        if self.fail_401_once:
            self.fail_401_once = False
            return httpx.Response(401, json={"error": "expired"}, request=req)

        if self.fail_429_once:
            self.fail_429_once = False
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate"}, request=req)

        if url.endswith('/v1/products/search'):
            return httpx.Response(
                200,
                json={"contents": [{"channelProductNo": "1001", "originProductNo": "9001", "name": "s1"}]},
                request=req,
            )
        if '/v2/products/channel-products/1001' in url:
            return httpx.Response(200, json={"name": "상품A", "salePrice": 19900, "productUrl": "https://smart/p/1001"}, request=req)
        if '/v2/products/origin-products/9001' in url:
            return httpx.Response(200, json={"name": "원상품A"}, request=req)

        return httpx.Response(404, json={"error": "notfound"}, request=req)


class TestMyStoreSync(unittest.TestCase):
    def test_issue_token(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        token = c.issue_token()
        self.assertEqual(token.access_token, "tok")


    def test_issue_token_form_encoded(self):
        class FormOnlyRequester(FakeRequester):
            def __call__(self, method, url, headers=None, json=None, data=None):
                req = httpx.Request(method, url)
                if url.endswith('/v1/oauth2/token'):
                    if (headers or {}).get('Content-Type') == 'application/x-www-form-urlencoded' and data:
                        return httpx.Response(200, json={"access_token": "tok-form", "expires_in": 10800}, request=req)
                    return httpx.Response(415, json={"error": "unsupported media type"}, request=req)
                return super().__call__(method, url, headers, json, data)

        r = FormOnlyRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        token = c.issue_token()
        self.assertEqual(token.access_token, "tok-form")

    def test_issue_token_form_fallback_to_json(self):
        class JsonOnlyRequester(FakeRequester):
            def __call__(self, method, url, headers=None, json=None, data=None):
                req = httpx.Request(method, url)
                if url.endswith('/v1/oauth2/token'):
                    if (headers or {}).get('Content-Type') == 'application/json' and json:
                        return httpx.Response(200, json={"access_token": "tok-json", "expires_in": 10800}, request=req)
                    return httpx.Response(415, json={"error": "unsupported media type"}, request=req)
                return super().__call__(method, url, headers, json, data)

        r = JsonOnlyRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        token = c.issue_token()
        self.assertEqual(token.access_token, "tok-json")

    def test_get_access_token_cached(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        t1 = c.get_access_token()
        t2 = c.get_access_token()
        self.assertEqual(t1, t2)
        self.assertEqual(len([x for x in r.calls if x[1].endswith('/v1/oauth2/token')]), 1)

    def test_search_products(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        data = c.search_products()
        self.assertTrue(data.get("contents"))

    def test_channel_detail(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        data = c.get_channel_product("1001")
        self.assertEqual(data["name"], "상품A")

    def test_origin_detail(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        data = c.get_origin_product("9001")
        self.assertEqual(data["name"], "원상품A")

    def test_retry_429(self):
        r = FakeRequester()
        r.fail_429_once = True
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        data = c.search_products()
        self.assertTrue(data.get("contents"))

    def test_retry_401_refresh_token(self):
        r = FakeRequester()
        r.fail_401_once = True
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        data = c.search_products()
        self.assertTrue(data.get("contents"))

    def test_fetch_enriched_products(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        rows = fetch_enriched_products(c)
        self.assertEqual(rows[0]["sku"], "1001")
        self.assertEqual(rows[0]["price"], 19900)


    def test_fetch_enriched_products_parallel_faster_than_serial(self):
        class SlowBatchRequester(FakeRequester):
            def __call__(self, method, url, headers=None, json=None, data=None):
                req = httpx.Request(method, url)
                if url.endswith('/v1/oauth2/token'):
                    return httpx.Response(200, json={"access_token": "tok", "expires_in": 10800}, request=req)
                if url.endswith('/v1/products/search'):
                    return httpx.Response(
                        200,
                        json={
                            "contents": [
                                {"channelProductNo": str(i), "originProductNo": str(9000 + i), "name": f"p{i}"}
                                for i in range(20)
                            ]
                        },
                        request=req,
                    )
                if '/v2/products/channel-products/' in url or '/v2/products/origin-products/' in url:
                    time.sleep(0.01)
                    return httpx.Response(200, json={"name": "상품", "salePrice": 1000, "productUrl": "https://smart/p"}, request=req)
                return super().__call__(method, url, headers, json, data)

        c = NaverCommerceClient("https://api", "id", "sec", requester=SlowBatchRequester())

        t0 = time.perf_counter()
        rows_serial = fetch_enriched_products(c, detail_workers=1)
        serial_elapsed = time.perf_counter() - t0

        t1 = time.perf_counter()
        rows_parallel = fetch_enriched_products(c, detail_workers=8)
        parallel_elapsed = time.perf_counter() - t1

        self.assertEqual(len(rows_serial), 20)
        self.assertEqual(len(rows_parallel), 20)
        self.assertLess(parallel_elapsed, serial_elapsed)

    def test_fetch_enriched_products_graceful_detail_fail(self):
        class FR(FakeRequester):
            def __call__(self, method, url, headers=None, json=None, data=None):
                if '/v2/products/channel-products/1001' in url:
                    req = httpx.Request(method, url)
                    return httpx.Response(500, json={"error": "boom"}, request=req)
                return super().__call__(method, url, headers, json, data)

        r = FR()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        rows = fetch_enriched_products(c)
        self.assertEqual(rows[0]["sku"], "1001")

    def test_sync_to_db_and_refresh_queue(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "blogs.db")
            repo = ProductRepo(db)
            result = sync_my_store_products(c, repo)
            self.assertEqual(result["fetched"], 1)
            with sqlite3.connect(db) as conn:
                cnt = conn.execute("SELECT COUNT(*) FROM products_ssot").fetchone()[0]
                self.assertEqual(cnt, 1)

    def test_sync_refresh_detects_change(self):
        r = FakeRequester()
        c = NaverCommerceClient("https://api", "id", "sec", requester=r)
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "blogs.db")
            repo = ProductRepo(db)
            sync_my_store_products(c, repo)
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE products SET price=10000 WHERE sku='1001'")
            res = sync_my_store_products(c, repo)
            self.assertIn("1001", res["refresh_queue"].get("skus", []))
            self.assertGreaterEqual(res["refresh_queue"].get("enqueued", 0), 1)
            queued = repo.get_refresh_queue_skus()
            self.assertIn("1001", queued)


if __name__ == "__main__":
    unittest.main()
