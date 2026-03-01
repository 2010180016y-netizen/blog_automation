import unittest
from app.eval.compliance import ComplianceEvaluator
from app.schemas import ComplianceRequest

class TestCompliance(unittest.TestCase):
    def setUp(self):
        self.evaluator = ComplianceEvaluator()

    def test_ko_clean_content(self):
        req = ComplianceRequest(content="이 제품은 정말 좋네요. 추천합니다.", language="ko")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "PASS")

    def test_ko_banned_word(self):
        req = ComplianceRequest(content="이 약은 무조건 완치 보장합니다.", language="ko")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")
        self.assertTrue(any(f['code'] == "KO_BANNED_CLAIM" for f in res.fail))

    def test_en_clean_content(self):
        req = ComplianceRequest(content="This product is great for daily use.", language="en")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "PASS")

    def test_en_banned_word(self):
        req = ComplianceRequest(content="This is a 100% cure for everything.", language="en")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")

    def test_ko_missing_disclosure(self):
        req = ComplianceRequest(content="리뷰입니다.", language="ko", is_sponsored=True)
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")


    def test_affiliate_disclosure_required_ko(self):
        req = ComplianceRequest(content="일반 소개 문구", language="ko", disclosure_required=True)
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")
        self.assertTrue(any(f['code'] == "KO_AFFILIATE_MISSING_DISCLOSURE" for f in res.fail))

    def test_affiliate_disclosure_required_en(self):
        req = ComplianceRequest(content="General review text", language="en", disclosure_required=True)
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")
        self.assertTrue(any(f['code'] == "EN_AFFILIATE_MISSING_DISCLOSURE" for f in res.fail))

    def test_ymyl_warning(self):
        req = ComplianceRequest(content="건강 정보입니다.", language="ko", category="건강")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "WARN")

if __name__ == "__main__":
    unittest.main()
