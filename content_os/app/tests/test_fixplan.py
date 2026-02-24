import unittest
from app.qa.fixplan import FixPlanGenerator

class TestFixPlan(unittest.TestCase):
    def setUp(self):
        self.generator = FixPlanGenerator()

    def test_generate_from_report(self):
        report = {
            "status": "REJECT",
            "fail": [
                {"code": "KO_BANNED_CLAIM", "detail": "무조건 발견", "location": "1문단"},
                {"code": "KO_MISSING_DISCLOSURE", "detail": "표기 누락", "location": "상단"}
            ],
            "warn": [
                {"code": "YMYL_MISSING_DISCLAIMER", "detail": "면책 누락", "location": "하단"}
            ]
        }
        
        res = self.generator.generate(report)
        
        self.assertEqual(res["total_count"], 3)
        self.assertIn("🚨 REJECT", res["markdown"])
        self.assertIn("⚠️ WARN", res["markdown"])
        self.assertIn("금지된 표현 수정", res["markdown"])
        
        # Check JSON structure
        self.assertEqual(res["json"][0]["code"], "KO_BANNED_CLAIM")
        self.assertEqual(res["json"][0]["severity"], "FAIL")

    def test_max_items_limit(self):
        config = {"qa_fixplan": {"rules": {"max_items": 1}}}
        generator = FixPlanGenerator(config)
        report = {
            "status": "REJECT",
            "fail": [
                {"code": "CODE1", "detail": "Detail 1"},
                {"code": "CODE2", "detail": "Detail 2"}
            ]
        }
        res = generator.generate(report)
        self.assertEqual(res["total_count"], 1)

if __name__ == "__main__":
    unittest.main()
