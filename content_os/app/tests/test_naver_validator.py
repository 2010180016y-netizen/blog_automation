import unittest
from app.seo.naver_validator import NaverValidator

class TestNaverValidator(unittest.TestCase):
    def setUp(self):
        self.validator = NaverValidator()

    def test_blog_spam_detection(self):
        # Content with repetitive words
        content = {
            "body": "애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플 애플",
            "links": [],
            "images": [{"is_unique": True}, {"is_unique": True}, {"is_unique": True}],
            "has_comparison_table": True
        }
        report = self.validator.validate_naver_blog_content(content)
        self.assertFalse(report["valid"])
        self.assertIn("Keyword stuffing", report["violations"][0])

    def test_commercial_balance(self):
        # High link density
        content = {
            "body": "This is a short text with many links.",
            "links": ["l1", "l2", "l3", "l4", "l5", "l6"],
            "images": [{"is_unique": True}, {"is_unique": True}, {"is_unique": True}],
            "has_comparison_table": True
        }
        report = self.validator.validate_naver_blog_content(content)
        self.assertFalse(report["valid"])
        self.assertIn("Too many links", report["violations"][0])

    def test_valid_naver_content(self):
        content = {
            "body": "이 제품은 실제 사용해보니 디자인이 매우 깔끔하고 성능이 뛰어납니다. 특히 배터리 수명이 길어서 하루 종일 사용해도 넉넉하네요.",
            "links": ["https://store.com/p1"],
            "images": [{"is_unique": True}, {"is_unique": True}, {"is_unique": True}],
            "has_comparison_table": True
        }
        report = self.validator.validate_naver_blog_content(content)
        self.assertTrue(report["valid"])

if __name__ == "__main__":
    unittest.main()
