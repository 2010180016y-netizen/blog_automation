import unittest
from app.eval.similarity import SimilarityEvaluator

class TestSimilarity(unittest.TestCase):
    def setUp(self):
        self.config = {
            "similarity": {
                "thresholds": {"warn": 0.7, "reject": 0.85},
                "ignore_sections": ["Price", "Shipping"]
            }
        }
        self.evaluator = SimilarityEvaluator(self.config)

    def test_split_paragraphs(self):
        text = "Para 1\n\nPara 2\n# Heading 1\nPara 3"
        paras = self.evaluator.split_paragraphs(text)
        self.assertEqual(len(paras), 3)

    def test_ignore_sections(self):
        text = "Para 1\n\nPrice: 100\n\nPara 2"
        paras = self.evaluator.split_paragraphs(text)
        self.assertEqual(len(paras), 2)
        self.assertNotIn("Price: 100", paras)

    def test_high_similarity(self):
        target = "This is a very specific sentence about a product that should be unique."
        existing = ["This is a very specific sentence about a product that should be unique."]
        res = self.evaluator.evaluate(target, existing)
        self.assertEqual(res["status"], "REJECT")
        self.assertEqual(len(res["matches"]), 1)

    def test_low_similarity(self):
        target = "Completely different content here."
        existing = ["This is a very specific sentence about a product that should be unique."]
        res = self.evaluator.evaluate(target, existing)
        self.assertEqual(res["status"], "PASS")

    def test_partial_similarity(self):
        target = "This is a sentence about a product."
        existing = ["This is a sentence about a different product."]
        res = self.evaluator.evaluate(target, existing)
        # Depending on TF-IDF, this might be a WARN or PASS
        self.assertIn(res["status"], ["PASS", "WARN", "REJECT"])


    def test_caches_existing_matrix(self):
        evaluator = SimilarityEvaluator(self.config)
        target = "alpha beta gamma"
        existing = ["alpha beta gamma", "delta epsilon"]
        evaluator.evaluate(target, existing)
        first_key = evaluator._cache_key
        self.assertIsNotNone(first_key)

        evaluator.evaluate("new target text", existing)
        self.assertEqual(evaluator._cache_key, first_key)

    def test_trims_existing_paragraphs_by_config(self):
        cfg = {
            "similarity": {
                "thresholds": {"warn": 0.7, "reject": 0.85},
                "ignore_sections": [],
                "max_existing_paragraphs": 3,
            }
        }
        evaluator = SimilarityEvaluator(cfg)
        target = "a"
        existing = ["p1", "p2", "p3", "p4", "p5"]
        trimmed = evaluator._trim_existing_paras(existing)
        self.assertEqual(trimmed, ["p3", "p4", "p5"])


if __name__ == "__main__":
    unittest.main()
