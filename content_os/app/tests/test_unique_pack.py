import unittest
import os
import shutil
import json
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
                "outputs": {"package_dir": "./test_out/packages"}
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

if __name__ == "__main__":
    unittest.main()
