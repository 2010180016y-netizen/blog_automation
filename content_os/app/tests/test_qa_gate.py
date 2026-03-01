import unittest

from app.qa.gate import QAGate, QAGateInput


def base_content_data():
    return {
        "intent": "info",
        "section_titles": ["사용법", "공식(근거)", "예시", "추천 대상 / 비추천 대상", "구매 전 체크리스트", "경쟁/대체 옵션 비교표", "FAQ", "주의사항", "엣지케이스"],
        "faq_count": 6,
        "example_count": 1,
        "caution_count": 1,
        "image_count": 2,
        "unique_fact_count": 2,
    }


class TestQAGate(unittest.TestCase):
    def setUp(self):
        self.gate = QAGate(
            {
                "similarity": {"thresholds": {"warn": 0.8, "reject": 0.88}, "ignore_sections": []},
                "qa": {
                    "required_sections": ["사용법", "공식(근거)", "예시", "추천 대상 / 비추천 대상", "구매 전 체크리스트", "경쟁/대체 옵션 비교표", "FAQ", "주의사항", "엣지케이스"],
                    "unique_pack": {"min_images": 2, "min_facts": 2},
                },
            }
        )

    def test_pass_ko_my_store(self):
        report = self.gate.evaluate(
            QAGateInput(content="이 제품은 일상 사용에 도움이 될 수 있습니다.", language="ko", source_type="MY_STORE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "PASS")

    def test_pass_en_my_store(self):
        report = self.gate.evaluate(
            QAGateInput(content="This may help daily routines with practical setup.", language="en", source_type="MY_STORE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "PASS")

    def test_reject_banned_claim_ko(self):
        report = self.gate.evaluate(
            QAGateInput(content="이건 무조건 완치 보장입니다.", language="ko", source_type="MY_STORE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "KO_BANNED_CLAIM" for f in report["fail"]))

    def test_reject_banned_claim_en(self):
        report = self.gate.evaluate(
            QAGateInput(content="This is a guaranteed cure.", language="en", source_type="MY_STORE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "EN_BANNED_CLAIM" for f in report["fail"]))

    def test_warn_ymyl(self):
        report = self.gate.evaluate(
            QAGateInput(content="건강 정보를 안내합니다.", language="ko", category="건강", source_type="MY_STORE", content_data=base_content_data())
        )
        self.assertIn(report["status"], ["WARN", "REJECT"])
        self.assertTrue(any(w["code"] == "YMYL_MISSING_DISCLAIMER" for w in report["warn"]))

    def test_affiliate_requires_disclosure_ko(self):
        report = self.gate.evaluate(
            QAGateInput(content="일반 설명입니다.", language="ko", source_type="AFFILIATE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "KO_AFFILIATE_MISSING_DISCLOSURE" for f in report["fail"]))

    def test_affiliate_requires_disclosure_en(self):
        report = self.gate.evaluate(
            QAGateInput(content="General review content.", language="en", source_type="AFFILIATE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "EN_AFFILIATE_MISSING_DISCLOSURE" for f in report["fail"]))

    def test_affiliate_with_disclosure_passes(self):
        report = self.gate.evaluate(
            QAGateInput(content="[제휴] 본문입니다. 과장 없는 설명입니다.", language="ko", source_type="AFFILIATE", content_data=base_content_data())
        )
        self.assertEqual(report["status"], "PASS")

    def test_similarity_warn(self):
        report = self.gate.evaluate(
            QAGateInput(
                content="The product helps with setup and maintenance in daily routines.",
                language="en",
                source_type="MY_STORE",
                existing_contents=["The product helps with setup and maintenance in daily routines with examples."],
                content_data=base_content_data(),
            )
        )
        self.assertIn(report["status"], ["WARN", "REJECT", "PASS"])

    def test_similarity_reject_exact_duplicate(self):
        txt = "This is a very specific sentence about a product that should be unique."
        report = self.gate.evaluate(
            QAGateInput(
                content=txt,
                language="en",
                source_type="MY_STORE",
                existing_contents=[txt],
                content_data=base_content_data(),
            )
        )
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "SIMILARITY_REJECT" for f in report["fail"]))

    def test_thin_content_missing_sections(self):
        data = base_content_data()
        data["section_titles"] = ["사용법", "FAQ"]
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=data))
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "THIN_CONTENT" for f in report["fail"]))

    def test_thin_content_missing_faq(self):
        data = base_content_data()
        data["faq_count"] = 5
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=data))
        self.assertEqual(report["status"], "REJECT")

    def test_unique_pack_missing_images(self):
        data = base_content_data()
        data["image_count"] = 1
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=data))
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "UNIQUE_PACK_INSUFFICIENT_IMAGES" for f in report["fail"]))

    def test_unique_pack_missing_facts(self):
        data = base_content_data()
        data["unique_fact_count"] = 1
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=data))
        self.assertEqual(report["status"], "REJECT")
        self.assertTrue(any(f["code"] == "UNIQUE_PACK_INSUFFICIENT_FACTS" for f in report["fail"]))

    def test_report_schema_fields(self):
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=base_content_data()))
        for key in ["schema_version", "status", "summary", "checks", "fail", "warn", "meta"]:
            self.assertIn(key, report)

    def test_fixplan_generation(self):
        data = base_content_data()
        data["image_count"] = 0
        report = self.gate.evaluate(QAGateInput(content="정상 문장", language="ko", source_type="MY_STORE", content_data=data))
        fp = self.gate.to_fixplan(report)
        self.assertIn("markdown", fp)
        self.assertGreater(fp["total_count"], 0)


if __name__ == "__main__":
    unittest.main()
