import unittest
import os
import shutil
import json
from unittest.mock import patch
from app.pipeline.unique_pack import UniquePackGenerator

class TestUniquePack(unittest.TestCase):
    def setUp(self):
        self.config = {
            "content_sources": {
                "image_assets_dir": "./test_assets/images",
                "video_assets_dir": "./test_assets/videos"
            },
            "unique_pack": {
                "required_per_post": {"min_images": 2},
                "outputs": {"package_dir": "./test_out/packages"},
                "quality": {
                    "max_duplicate_ratio": 0.6,
                    "alt_min_chars": 5,
                    "alt_max_chars": 120,
                    "alt_required_phrases": []
                }
            }
        }
        os.makedirs("./test_assets/images/SKU001", exist_ok=True)
        with open("./test_assets/images/SKU001/img1.jpg", "w") as f: f.write("fake image 1")
        with open("./test_assets/images/SKU001/img2.jpg", "w") as f: f.write("fake image 2")
        
        self.generator = UniquePackGenerator(self.config)

    def tearDown(self):
        if os.path.exists("./test_assets"): shutil.rmtree("./test_assets")
        if os.path.exists("./test_out"): shutil.rmtree("./test_out")

    def test_pass_with_images(self):
        res = self.generator.process("SKU001", "POST001")
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(os.path.exists("./test_out/packages/POST001/unique_facts.json"))
        self.assertTrue(os.path.exists("./test_out/packages/POST001/image_optimization_report.json"))

    def test_reject_insufficient_images(self):
        os.makedirs("./test_assets/images/SKU002", exist_ok=True)
        with open("./test_assets/images/SKU002/img1.jpg", "w") as f: f.write("fake image 1")
        res = self.generator.process("SKU002", "POST002")
        self.assertEqual(res["status"], "REJECT")


    def test_reject_duplicate_ratio_too_high(self):
        with open("./test_assets/images/SKU001/img3.jpg", "w") as f: f.write("fake image 1")
        strict_config = dict(self.config)
        strict_config["unique_pack"] = dict(self.config["unique_pack"])
        strict_config["unique_pack"]["quality"] = dict(self.config["unique_pack"]["quality"])
        strict_config["unique_pack"]["quality"]["max_duplicate_ratio"] = 0.2
        generator = UniquePackGenerator(strict_config)

        with patch("app.pipeline.unique_pack.optimize_image_asset", side_effect=lambda img, out: {"output": img, "format": "jpg"}):
            with patch("app.pipeline.unique_pack.generate_alt_text", return_value="상품 상세 이미지"):
                res = generator.process("SKU001", "POST003")

        self.assertEqual(res["status"], "REJECT")
        self.assertIn("Duplicate ratio too high", res["reason"])

    def test_reject_alt_policy_required_phrase(self):
        strict_config = dict(self.config)
        strict_config["unique_pack"] = dict(self.config["unique_pack"])
        strict_config["unique_pack"]["quality"] = dict(self.config["unique_pack"]["quality"])
        strict_config["unique_pack"]["quality"]["alt_required_phrases"] = ["상품"]
        generator = UniquePackGenerator(strict_config)

        with patch("app.pipeline.unique_pack.optimize_image_asset", side_effect=lambda img, out: {"output": img, "format": "jpg"}):
            with patch("app.pipeline.unique_pack.generate_alt_text", return_value="bad alt text"):
                res = generator.process("SKU001", "POST004")
        self.assertEqual(res["status"], "REJECT")
        self.assertIn("required phrase", res["reason"])


if __name__ == "__main__":
    unittest.main()
