import unittest
from app.store.insights import InsightExtractor
from app.store.update_pack import StoreUpdatePackGenerator

class TestStorePack(unittest.TestCase):
    def setUp(self):
        self.config = {
            "store_improve": {
                "sources": ["blog_faq", "comments"],
                "pack_fields": ["top_questions", "warnings"]
            }
        }
        self.extractor = InsightExtractor(self.config)
        self.generator = StoreUpdatePackGenerator(self.config)

    def test_insight_extraction(self):
        data = [
            {"type": "blog_faq", "text": "배송은 얼마나 걸리나요?", "count": 10},
            {"type": "comments", "text": "사이즈가 좀 작아요", "tags": ["warning"], "count": 5},
            {"type": "cs_log", "text": "환불하고 싶어요", "count": 2} # Not in sources
        ]
        
        questions = self.extractor.extract_top_questions(data)
        warnings = self.extractor.extract_warnings(data)
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["question"], "배송은 얼마나 걸리나요?")
        self.assertIn("사이즈가 좀 작아요", warnings)

    def test_pack_generation(self):
        insights = {
            "top_questions": [{"question": "How to use?", "frequency": 5}],
            "warnings": ["Keep away from water"]
        }
        pack = self.generator.generate_pack("SKU123", insights)
        
        self.assertEqual(pack["sku"], "SKU123")
        self.assertIn("qna", pack["content"])
        self.assertIn("warnings", pack["content"])
        self.assertEqual(pack["content"]["qna"][0]["q"], "How to use?")

if __name__ == "__main__":
    unittest.main()
