import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_track
from app.track.event_collector import EventCollector


class TestTrackAPI(unittest.TestCase):
    def test_build_link_endpoint_records_event(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "track.db")
            original_collector = routes_track.collector
            routes_track.collector = EventCollector(db)
            try:
                client = TestClient(app)
                payload = {
                    "base_url": "https://smartstore.naver.com/test",
                    "channel": "naver",
                    "content_id": "post-1",
                    "sku": "sku-1",
                    "intent": "buy",
                }
                res = client.post("/track/link", json=payload)
                self.assertEqual(res.status_code, 200)
                body = res.json()
                self.assertEqual(body["status"], "ok")
                self.assertIn("ch=naver", body["tracking_url"])
                self.assertIn("cid=post-1", body["tracking_url"])

                events = routes_track.collector.get_events({"event_type": "link_built"})
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["content_id"], "post-1")
            finally:
                routes_track.collector = original_collector


if __name__ == "__main__":
    unittest.main()
