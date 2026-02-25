import os
import unittest

from app.publish.state_machine import ContentState
from app.publish.queue import PublishQueue, SQLiteQueueStorage


class TestPublishFlow(unittest.TestCase):
    def setUp(self):
        self.config = {
            "publishing": {
                "governance": {
                    "require_human_approval_for": ["naver"]
                }
            }
        }
        self.db_path = "test_publish_queue.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.storage = SQLiteQueueStorage(self.db_path)
        self.queue = PublishQueue(self.config, storage=self.storage)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_state_transitions(self):
        self.queue.add_item("POST001", {"platform": "wordpress"})

        # DRAFT -> QA_PASS
        self.queue.update_state("POST001", ContentState.QA_PASS)
        self.assertEqual(self.queue.items["POST001"]["state"], ContentState.QA_PASS)

        # QA_PASS -> READY
        self.queue.update_state("POST001", ContentState.READY)
        self.assertEqual(self.queue.items["POST001"]["state"], ContentState.READY)

        # Invalid transition: READY -> DRAFT
        with self.assertRaises(ValueError):
            self.queue.update_state("POST001", ContentState.DRAFT)

    def test_human_approval_governance(self):
        # Naver requires approval
        self.queue.add_item("NAVER001", {"platform": "naver"})
        self.queue.update_state("NAVER001", ContentState.QA_PASS)
        self.queue.update_state("NAVER001", ContentState.READY)

        self.assertTrue(self.queue.items["NAVER001"]["human_approval_required"])

        # Should not be in ready items until approved
        ready = self.queue.get_ready_items("naver")
        self.assertEqual(len(ready), 0)

        self.queue.approve("NAVER001")
        ready = self.queue.get_ready_items("naver")
        self.assertEqual(len(ready), 1)

    def test_wordpress_no_approval(self):
        # WP does not require approval in this config
        self.queue.add_item("WP001", {"platform": "wordpress"})
        self.queue.update_state("WP001", ContentState.QA_PASS)
        self.queue.update_state("WP001", ContentState.READY)

        self.assertFalse(self.queue.items["WP001"]["human_approval_required"])
        ready = self.queue.get_ready_items("wordpress")
        self.assertEqual(len(ready), 1)

    def test_state_persisted_across_queue_restart(self):
        self.queue.add_item("PERSIST001", {"platform": "naver", "title": "t1"})
        self.queue.update_state("PERSIST001", ContentState.QA_PASS)
        self.queue.update_state("PERSIST001", ContentState.READY)

        # Simulate process restart with same storage
        restarted_queue = PublishQueue(self.config, storage=SQLiteQueueStorage(self.db_path))

        self.assertIn("PERSIST001", restarted_queue.items)
        item = restarted_queue.items["PERSIST001"]
        self.assertEqual(item["state"], ContentState.READY)
        self.assertEqual(item["history"], [ContentState.DRAFT, ContentState.QA_PASS, ContentState.READY])
        self.assertTrue(item["human_approval_required"])

        restarted_queue.approve("PERSIST001")
        reopened_queue = PublishQueue(self.config, storage=SQLiteQueueStorage(self.db_path))
        self.assertFalse(reopened_queue.items["PERSIST001"]["human_approval_required"])


if __name__ == "__main__":
    unittest.main()
