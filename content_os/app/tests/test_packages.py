import unittest
import os
import json
import shutil
from app.packages.registry import PackageRegistry
from app.packages.loader import PackageLoader
from app.packages.schema import PackageManifest, PackageMetadata

class TestPackages(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_packages_root"
        os.makedirs(self.test_dir, exist_ok=True)
        self.registry = PackageRegistry()
        self.loader = PackageLoader(self.test_dir, self.registry)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_package_lifecycle(self):
        # 1. Create a mock package on disk
        pkg_name = "beauty_ko"
        version = "1.0.0"
        pkg_root = os.path.join(self.test_dir, pkg_name, version)
        os.makedirs(pkg_root, exist_ok=True)
        
        template_content = "<html>Beauty Template</html>"
        with open(os.path.join(pkg_root, "template.html"), "w") as f:
            f.write(template_content)
            
        manifest_data = {
            "metadata": {
                "name": pkg_name,
                "version": version,
                "category": "beauty",
                "includes": ["templates"]
            },
            "content_map": {
                "main_template": "template.html"
            }
        }
        with open(os.path.join(pkg_root, "manifest.json"), "w") as f:
            json.dump(manifest_data, f)

        # 2. Scan and Register
        self.loader.scan_and_load()
        
        # 3. Verify Registry
        pkg = self.registry.get_package(pkg_name)
        self.assertIsNotNone(pkg)
        self.assertEqual(pkg.metadata.version, version)
        
        # 4. Load Resource
        content = self.loader.load_resource(pkg, "main_template")
        self.assertEqual(content, template_content)

if __name__ == "__main__":
    unittest.main()
