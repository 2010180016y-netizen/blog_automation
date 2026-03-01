import json
import os
import tempfile
import unittest

from app.publish.naver_package import NaverPackageGenerator


class TestNaverPackageGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gen = NaverPackageGenerator(output_root=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _read(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_create_package_info_pass(self):
        res = self.gen.create_package(
            content_id="C1",
            product_id="P1",
            source_type="MY_STORE",
            intent="info",
            cta_link="https://example.com/p1",
        )
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(os.path.exists(res["post_html"]))
        self.assertTrue(os.path.exists(res["meta_json"]))

    def test_required_sections_present(self):
        res = self.gen.create_package(
            content_id="C2",
            product_id="P2",
            source_type="MY_STORE",
            intent="compare",
            cta_link="https://example.com/p2",
        )
        html = self._read(res["post_html"])
        for sec in ["사용법", "공식(근거)", "예시", "추천 대상 / 비추천 대상", "구매 전 체크리스트", "경쟁/대체 옵션 비교표", "FAQ", "주의사항", "엣지케이스"]:
            self.assertIn(f"<h2>{sec}</h2>", html)

    def test_affiliate_disclosure_included(self):
        res = self.gen.create_package(
            content_id="C3",
            product_id="P3",
            source_type="AFFILIATE",
            intent="review",
            cta_link="https://example.com/p3",
        )
        html = self._read(res["post_html"])
        self.assertIn("[제휴 안내]", html)
        self.assertIn("가격/혜택은 시점에 따라 변동될 수 있습니다", html)

    def test_meta_json_has_required_fields(self):
        res = self.gen.create_package(
            content_id="C4",
            product_id="P4",
            source_type="MY_STORE",
            intent="story",
            cta_link="https://example.com/p4",
        )
        data = json.loads(self._read(res["meta_json"]))
        for key in ["title", "summary", "tags", "category", "cta_link", "content_id", "product_id", "source_type", "intent", "variant"]:
            self.assertIn(key, data)

    def test_images_placeholder_created(self):
        res = self.gen.create_package(
            content_id="C5",
            product_id="P5",
            source_type="MY_STORE",
            intent="info",
            cta_link="https://example.com/p5",
        )
        files = sorted(os.listdir(res["images_dir"]))
        self.assertEqual(files, ["placeholder_1.txt", "placeholder_2.txt", "placeholder_3.txt"])

    def test_faq_minimum_six(self):
        res = self.gen.create_package(
            content_id="C8",
            product_id="P8",
            source_type="MY_STORE",
            intent="review",
            cta_link="https://example.com/p8",
        )
        html = self._read(res["post_html"])
        self.assertGreaterEqual(html.count("<li>Q."), 6)

    def test_ab_variants_generated_with_variant_param(self):
        res = self.gen.create_ab_variants(
            content_id="CAB",
            product_id="PAB",
            source_type="MY_STORE",
            intent="info",
            cta_link="https://example.com/pab",
        )
        self.assertEqual(res["variants"]["A"]["status"], "PASS")
        self.assertEqual(res["variants"]["B"]["status"], "PASS")

        meta_a = json.loads(self._read(res["variants"]["A"]["meta_json"]))
        meta_b = json.loads(self._read(res["variants"]["B"]["meta_json"]))
        self.assertIn("variant=A", meta_a["cta_link"])
        self.assertIn("variant=B", meta_b["cta_link"])
        self.assertTrue(os.path.basename(res["variants"]["A"]["package_dir"]).endswith("_A"))
        self.assertTrue(os.path.basename(res["variants"]["B"]["package_dir"]).endswith("_B"))

    def test_variant_a_and_b_have_different_cta_position_or_copy(self):
        a = self.gen.create_package("CV1", "P1", "MY_STORE", "info", "https://example.com/1", variant="A")
        b = self.gen.create_package("CV1", "P1", "MY_STORE", "info", "https://example.com/1", variant="B")
        html_a = self._read(a["post_html"])
        html_b = self._read(b["post_html"])
        self.assertIn("지금 혜택 확인하기", html_a)
        self.assertIn("최신 가격/리뷰 보고 결정하기", html_b)


    def test_package_write_skipped_when_unchanged(self):
        first = self.gen.create_package(
            content_id="CSKIP",
            product_id="PSKIP",
            source_type="MY_STORE",
            intent="info",
            cta_link="https://example.com/skip",
            variant="A",
        )
        self.assertTrue(first["io"]["wrote_post_html"])
        self.assertTrue(first["io"]["wrote_meta_json"])

        second = self.gen.create_package(
            content_id="CSKIP",
            product_id="PSKIP",
            source_type="MY_STORE",
            intent="info",
            cta_link="https://example.com/skip",
            variant="A",
        )
        self.assertFalse(second["io"]["wrote_post_html"])
        self.assertFalse(second["io"]["wrote_meta_json"])

    def test_invalid_intent_raises(self):
        with self.assertRaises(ValueError):
            self.gen.create_package(
                content_id="C6",
                product_id="P6",
                source_type="MY_STORE",
                intent="invalid",  # type: ignore[arg-type]
                cta_link="https://example.com/p6",
            )

    def test_invalid_source_type_raises(self):
        with self.assertRaises(ValueError):
            self.gen.create_package(
                content_id="C7",
                product_id="P7",
                source_type="OTHER",  # type: ignore[arg-type]
                intent="info",
                cta_link="https://example.com/p7",
            )

    def test_qareject_when_missing_sections(self):
        bad_html = "<article><h2>사용법</h2></article>"
        qa = self.gen._validate_required_sections(bad_html, source_type="MY_STORE")
        self.assertEqual(qa["status"], "REJECT")
        self.assertIn("공식(근거)", qa["missing_sections"])


if __name__ == "__main__":
    unittest.main()
