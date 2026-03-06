import tempfile
import unittest
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
        self.assertTrue(any(f["code"] == "KO_BANNED_CLAIM" for f in res.fail))

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

    def test_affiliate_link_requires_nearby_disclosure(self):
        req = ComplianceRequest(
            content="[Disclosure] sponsored content. xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\nRead more: https://amzn.to/abc123",
            language="en",
            disclosure_required=True,
        )
        res = self.evaluator.evaluate(req)
        self.assertEqual(res.status, "REJECT")
        self.assertTrue(any(f["code"] == "EN_AFFILIATE_DISCLOSURE_MISSING" for f in res.fail))

    def test_apply_disclosures_inserts_templates(self):
        patched = self.evaluator.apply_disclosures(
            title="Best Air Purifier Review",
            content="Buy here: https://amzn.to/abc123",
            language="en",
            disclosure_required=True,
        )
        self.assertIn("Sponsored/Affiliate Disclosure", patched["title"])
        self.assertIn("[Disclosure]", patched["content"])
        self.assertIn("Disclosure: We may earn a commission", patched["content"])

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
  affiliate_domains: ["amzn.to"]
  affiliate_disclosure_window_chars: 200
  disclosure_templates:
    ko:
      title_prefix: "[광고]"
      body_prefix: "[광고 고지]"
    en:
      title_prefix: "[Sponsored]"
      body_prefix: "[Disclosure]"
  affiliate_link_disclosures:
    ko: "제휴 링크 고지"
    en: "Affiliate link disclosure"
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
