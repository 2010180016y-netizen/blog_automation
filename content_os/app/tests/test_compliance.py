import unittest
import tempfile
from pathlib import Path
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

    def test_ymyl_warning(self):
        req = ComplianceRequest(content="건강 정보입니다.", language="ko", category="건강")
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "WARN")

    def test_ruleset_path_override(self):
        custom_yaml = """
version: "test.v1"
compliance:
  categories: ["테스트"]
  banned_claims:
    ko: ["절대금지단어"]
    en: ["forbiddenword"]
  required_disclosures:
    ko: ["광고"]
    en: ["sponsored"]
"""
        with tempfile.TemporaryDirectory() as td:
            rules_path = Path(td) / "rules.yaml"
            rules_path.write_text(custom_yaml, encoding="utf-8")
            evaluator = ComplianceEvaluator(ruleset_path=str(rules_path))
            req = ComplianceRequest(content="절대금지단어 포함", language="ko")
            res = evaluator.evaluate(req)
            self.assertEqual(res.status, "REJECT")
            self.assertTrue(any("RULESET_VERSION=test.v1" == s for s in res.suggestions))

if __name__ == "__main__":
    unittest.main()
