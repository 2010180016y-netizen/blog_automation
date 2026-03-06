import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_ingest


class TestIngestAPISecurity(unittest.TestCase):
    def setUp(self):
        routes_ingest._limiter._events.clear()
        self.client = TestClient(app)
        self.payload = {
            "base_url": "https://api.example.com",
            "client_id": "id",
            "client_secret": "sec",
            "db_path": str(Path(tempfile.gettempdir()) / "ingest-api-test.db"),
            "page": 1,
            "size": 10,
        }

    @patch("app.api.routes_ingest.sync_my_store_products")
    def test_requires_auth(self, mock_sync):
        mock_sync.return_value = {"fetched": 0, "ssot": {}, "refresh_queue": {}}
        with patch.dict(os.environ, {}, clear=False):
            resp = self.client.post("/ingest/my-store/sync", json=self.payload)
        self.assertEqual(resp.status_code, 503)

    @patch("app.api.routes_ingest.sync_my_store_products")
    def test_accepts_api_key(self, mock_sync):
        mock_sync.return_value = {"fetched": 1, "ssot": {}, "refresh_queue": {"count": 0, "skus": []}}
        with patch.dict(os.environ, {"INGEST_API_KEY": "k1", "INGEST_RATE_LIMIT_PER_MINUTE": "10"}, clear=False):
            resp = self.client.post("/ingest/my-store/sync", json=self.payload, headers={"X-API-Key": "k1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["fetched"], 1)

    @patch("app.api.routes_ingest.sync_my_store_products")
    def test_rate_limit_blocks_excess(self, mock_sync):
        mock_sync.return_value = {"fetched": 1, "ssot": {}, "refresh_queue": {"count": 0, "skus": []}}
        with patch.dict(os.environ, {"INGEST_API_KEY": "k1", "INGEST_RATE_LIMIT_PER_MINUTE": "1"}, clear=False):
            first = self.client.post("/ingest/my-store/sync", json=self.payload, headers={"X-API-Key": "k1"})
            second = self.client.post("/ingest/my-store/sync", json=self.payload, headers={"X-API-Key": "k1"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    @patch("app.api.routes_ingest.sync_my_store_products")
    def test_audit_log_emitted(self, mock_sync):
        mock_sync.return_value = {"fetched": 2, "ssot": {}, "refresh_queue": {"count": 1, "skus": ["S1"]}}
        with patch.dict(os.environ, {"INGEST_API_KEY": "k1", "INGEST_RATE_LIMIT_PER_MINUTE": "10"}, clear=False):
            with self.assertLogs("content_os.audit.ingest", level="INFO") as cm:
                resp = self.client.post("/ingest/my-store/sync", json=self.payload, headers={"X-API-Key": "k1"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any("ingest_my_store_sync" in line for line in cm.output))


if __name__ == "__main__":
    unittest.main()
