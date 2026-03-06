import unittest

from app.content.naver.generator import generate_naver_affiliate_package


class TestNaverGenerator(unittest.TestCase):
    def test_cro_sections_and_dates_present(self):
        pkg = generate_naver_affiliate_package(
            {
                "partner_product_id": "PT-1",
                "title": "테스트 상품",
                "affiliate_link": "https://shoppingconnect.link/abc",
                "written_date": "2026-01-01",
                "updated_date": "2026-01-02",
                "ab_variant": "B",
            }
        )
        html = pkg["html"]
        self.assertIn("추천 대상 / 비추천 대상", html)
        self.assertIn("선택 체크리스트", html)
        self.assertIn("대체 상품 비교표", html)
        self.assertIn("작성일: 2026-01-01", html)
        self.assertIn("업데이트일: 2026-01-02", html)
        self.assertEqual(pkg["ab_variant"], "B")
        self.assertTrue(pkg.get("template"))


if __name__ == "__main__":
    unittest.main()
