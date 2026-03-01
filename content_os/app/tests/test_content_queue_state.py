import os
import sqlite3
import tempfile
import unittest

from app.publish.content_queue_state import ContentQueueService, QueueState


class TestContentQueueState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "queue.db")
        self.svc = ContentQueueService(db_path=self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _mk_item(self):
        return self.svc.create_item("SKU1", "info", "MY_STORE", True, {"k": "v"})

    def test_create_item_defaults_draft(self):
        item_id = self._mk_item()
        row = self.svc.get_item(item_id)
        self.assertEqual(row["status"], "DRAFT")

    def test_valid_transition_draft_to_qapass(self):
        item_id = self._mk_item()
        res = self.svc.transition(item_id, QueueState.QA_PASS)
        self.assertEqual(res.to_state, QueueState.QA_PASS)

    def test_invalid_transition_draft_to_ready_blocked(self):
        item_id = self._mk_item()
        with self.assertRaises(ValueError):
            self.svc.transition(item_id, QueueState.READY)

    def test_valid_transition_qapass_to_ready(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        res = self.svc.transition(item_id, QueueState.READY)
        self.assertEqual(res.to_state, QueueState.READY)

    def test_valid_transition_ready_to_published(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        self.svc.transition(item_id, QueueState.READY)
        res = self.svc.transition(item_id, QueueState.PUBLISHED)
        self.assertEqual(res.to_state, QueueState.PUBLISHED)

    def test_reject_from_draft(self):
        item_id = self._mk_item()
        res = self.svc.transition(item_id, QueueState.REJECTED)
        self.assertEqual(res.to_state, QueueState.REJECTED)

    def test_reject_from_qapass(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        res = self.svc.transition(item_id, QueueState.REJECTED)
        self.assertEqual(res.to_state, QueueState.REJECTED)

    def test_reject_from_ready(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        self.svc.transition(item_id, QueueState.READY)
        res = self.svc.transition(item_id, QueueState.REJECTED)
        self.assertEqual(res.to_state, QueueState.REJECTED)

    def test_published_cannot_transition_directly(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        self.svc.transition(item_id, QueueState.READY)
        self.svc.transition(item_id, QueueState.PUBLISHED)
        with self.assertRaises(ValueError):
            self.svc.transition(item_id, QueueState.REJECTED)

    def test_refresh_only_for_published(self):
        item_id = self._mk_item()
        with self.assertRaises(ValueError):
            self.svc.request_refresh_for_published(item_id, reason="UPDATE")

    def test_refresh_for_published_inserts_queue(self):
        item_id = self._mk_item()
        self.svc.transition(item_id, QueueState.QA_PASS)
        self.svc.transition(item_id, QueueState.READY)
        self.svc.transition(item_id, QueueState.PUBLISHED)
        rid = self.svc.request_refresh_for_published(item_id, reason="PRICE_CHANGED", payload={"x": 1})
        self.assertGreater(rid, 0)
        conn = sqlite3.connect(self.db_path)
        try:
            n = conn.execute("SELECT COUNT(*) FROM refresh_queue").fetchone()[0]
            self.assertEqual(n, 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
