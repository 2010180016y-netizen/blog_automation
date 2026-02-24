import unittest
from datetime import datetime, timedelta
from app.refresh.detector import RefreshDetector
from app.refresh.update_pack import UpdatePackGenerator

class TestRefresh(unittest.TestCase):
    def setUp(self):
        self.config = {"refresh": {"rules": {"stale_days": 30}}}
        self.detector = RefreshDetector(self.config)
        self.generator = UpdatePackGenerator()

    def test_stale_detection(self):
        content = [
            {"id": "C1", "published_at": (datetime.now() - timedelta(days=40)).isoformat()},
            {"id": "C2", "published_at": (datetime.now() - timedelta(days=10)).isoformat()}
        ]
        stale = self.detector.detect_stale_content(content)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["id"], "C1")

    def test_product_change_detection(self):
        content = [{"id": "C1", "sku": "S1", "product_hash": "old_hash"}]
        db = {"S1": {"hash": "new_hash", "diff_summary": "Price dropped"}}
        changed = self.detector.detect_product_changes(content, db)
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0]["reason"], "PRODUCT_INFO_CHANGED")

    def test_update_pack_generation(self):
        pack = self.generator.generate_pack("C1", "STALE_CONTENT", {"days_old": 45})
        self.assertEqual(pack["content_id"], "C1")
        self.assertEqual(len(pack["proposed_changes"]), 1)

if __name__ == "__main__":
    unittest.main()
