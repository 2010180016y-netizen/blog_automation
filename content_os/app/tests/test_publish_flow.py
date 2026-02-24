import unittest
from app.publish.state_machine import StateMachine, ContentState
from app.publish.queue import PublishQueue

class TestPublishFlow(unittest.TestCase):
    def setUp(self):
        self.config = {
            "publishing": {
                "governance": {
                    "require_human_approval_for": ["naver"]
                }
            }
        }
        self.queue = PublishQueue(self.config)

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

if __name__ == "__main__":
    unittest.main()
