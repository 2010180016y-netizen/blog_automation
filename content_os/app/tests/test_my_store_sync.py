import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import httpx

from app.store.my_store_sync import MyStoreRepository, MyStoreSyncService, TokenState


class TestMyStoreSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "sync.db")
        self.repo = MyStoreRepository(db_path=self.db_path)
        self.client = MagicMock()
        self.now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.sleeps = []
        self.service = MyStoreSyncService(
            repo=self.repo,
            client=self.client,
            now_fn=lambda: self.now,
            sleep_fn=lambda s: self.sleeps.append(s),
            max_retries=2,
            backoff_seconds=0.1,
            concurrency=2,
        )
        self.service.token_url = "https://auth.example.com/token"
        self.service.api_base_url = "https://api.example.com"
        self.service.client_id = "cid"
        self.service.client_secret = "sec"

    def tearDown(self):
        self.tmpdir.cleanup()

    def _response(self, code=200, payload=None):
        req = httpx.Request("GET", "https://x")
        return httpx.Response(code, json=payload or {}, request=req)

    def test_token_cached(self):
        self.client.request.return_value = self._response(payload={"access_token": "t1", "expires_in": 3600})
        t1 = self.service.get_access_token()
        t2 = self.service.get_access_token()
        self.assertEqual(t1, "t1")
        self.assertEqual(t2, "t1")
        self.assertEqual(self.client.request.call_count, 1)

    def test_token_refresh_when_expired(self):
        self.service._token_state = TokenState("old", self.now + timedelta(seconds=30))
        self.client.request.return_value = self._response(payload={"access_token": "new", "expires_in": 3600})
        self.assertEqual(self.service.get_access_token(), "new")

    def test_retry_on_429_then_success(self):
        self.client.request.side_effect = [
            self._response(429, {}),
            self._response(200, {"ok": True}),
        ]
        res = self.service._request_with_retry("GET", "https://api.example.com/products")
        self.assertEqual(res.json()["ok"], True)
        self.assertEqual(self.client.request.call_count, 2)
        self.assertEqual(self.sleeps, [0.1])

    def test_retry_exhaust_raises(self):
        self.client.request.side_effect = [
            self._response(503, {}),
            self._response(503, {}),
            self._response(503, {}),
        ]
        with self.assertRaises(httpx.HTTPStatusError):
            self.service._request_with_retry("GET", "https://api.example.com/products")

    def test_fetch_product_ids_pagination_has_more(self):
        self.service.get_access_token = MagicMock(return_value="token")
        self.client.request.side_effect = [
            self._response(payload={"products": [{"id": "1"}], "has_more": True}),
            self._response(payload={"products": [{"id": "2"}], "has_more": False}),
        ]
        ids = self.service.fetch_product_ids()
        self.assertEqual(ids, ["1", "2"])

    def test_fetch_product_ids_with_cursor(self):
        self.service.get_access_token = MagicMock(return_value="token")
        self.client.request.side_effect = [
            self._response(payload={"items": [{"product_id": "a"}], "next_cursor": "c1"}),
            self._response(payload={"items": [{"product_id": "b"}]}),
        ]
        ids = self.service.fetch_product_ids()
        self.assertEqual(ids, ["a", "b"])

    def test_parse_product_success(self):
        detail = {"sku": "SKU1", "name": "P1", "price": 1000, "currency": "KRW", "status": "ON"}
        row = self.service.parse_product("101", detail)
        self.assertEqual(row["sku"], "SKU1")
        self.assertEqual(row["parse_status"], "OK")
        self.assertIn("raw_json", row)

    def test_parse_product_graceful_fail(self):
        class BrokenDict(dict):
            def get(self, key, default=None):
                if key == "sku":
                    raise ValueError("broken")
                return super().get(key, default)

        row = self.service.parse_product("101", BrokenDict({"name": "P1"}))
        self.assertEqual(row["parse_status"], "PARSE_FAIL")
        self.assertEqual(row["sku"], "101")
        self.assertTrue(row["parse_error"])


    def test_repo_indexes_created(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        names = {r[0] for r in rows}
        self.assertIn("idx_my_store_products_product_id", names)
        self.assertIn("idx_my_store_products_payload_hash", names)
        self.assertIn("idx_refresh_queue_sku_status", names)

    def test_batch_upsert_and_hash_lookup(self):
        rows = [
            {
                "sku": "S1",
                "product_id": "1",
                "title": "T",
                "price": 1,
                "currency": "KRW",
                "status": "ON",
                "payload_hash": "h1",
                "raw_json": "{}",
                "parse_status": "OK",
                "parse_error": None,
            }
        ]
        n = self.repo.batch_upsert_products(rows)
        hashes = self.repo.get_hashes(["S1"])
        self.assertEqual(n, 1)
        self.assertEqual(hashes["S1"], "h1")

    def test_refresh_queue_for_new_and_changed(self):
        initial = {
            "sku": "S1",
            "product_id": "1",
            "title": "T",
            "price": 1,
            "currency": "KRW",
            "status": "ON",
            "payload_hash": "h1",
            "raw_json": "{}",
            "parse_status": "OK",
            "parse_error": None,
        }
        self.repo.batch_upsert_products([initial])

        rows = [
            dict(initial),
            {
                **initial,
                "sku": "S2",
                "product_id": "2",
                "payload_hash": "h2",
            },
            {
                **initial,
                "sku": "S1",
                "payload_hash": "h1-new",
            },
        ]
        entries = self.service._build_refresh_entries(rows)
        reasons = {(s, r) for s, r, _ in entries}
        self.assertIn(("S2", "NEW_PRODUCT"), reasons)
        self.assertIn(("S1", "PRODUCT_CHANGED"), reasons)

    def test_sync_end_to_end(self):
        self.client.request.side_effect = [
            self._response(payload={"access_token": "tok", "expires_in": 3600}),
            self._response(payload={"products": [{"id": "p1"}, {"id": "p2"}], "has_more": False}),
            self._response(payload={"sku": "S1", "name": "N1", "price": 10, "status": "ON"}),
            self._response(payload={"sku": "S2", "name": "N2", "price": 20, "status": "ON"}),
        ]
        result = self.service.sync()
        self.assertEqual(result["fetched"], 2)
        self.assertEqual(result["upserted"], 2)
        self.assertEqual(result["queued"], 2)
        self.assertEqual(result["errors"], 0)


    def test_sync_returns_timings(self):
        self.client.request.side_effect = [
            self._response(payload={"access_token": "tok", "expires_in": 3600}),
            self._response(payload={"products": [{"id": "p1"}], "has_more": False}),
            self._response(payload={"sku": "S1", "name": "N1", "price": 10, "status": "ON"}),
        ]
        result = self.service.sync()
        self.assertIn("timings", result)
        self.assertIn("fetch_ids_sec", result["timings"])
        self.assertIn("fetch_details_sec", result["timings"])
        self.assertIn("db_upsert_enqueue_sec", result["timings"])
        self.assertIn("total_sec", result["timings"])

    def test_sync_handles_detail_failure(self):
        self.client.request.side_effect = [
            self._response(payload={"access_token": "tok", "expires_in": 3600}),
            self._response(payload={"products": [{"id": "p1"}], "has_more": False}),
            self._response(500, {}),
            self._response(500, {}),
            self._response(500, {}),
        ]
        result = self.service.sync()
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["upserted"], 0)


if __name__ == "__main__":
    unittest.main()
