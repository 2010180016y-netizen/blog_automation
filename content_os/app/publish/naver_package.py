import os
import json
import zipfile
from typing import Dict

class NaverPackageGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def create_package(self, content_id: str, title: str, body_html: str, images: list, metadata: Dict) -> str:
        package_path = os.path.join(self.output_dir, f"naver_{content_id}")
        os.makedirs(package_path, exist_ok=True)
        
        # 1. Save content as HTML
        with open(os.path.join(package_path, "content.html"), "w", encoding="utf-8") as f:
            f.write(f"<h1>{title}</h1>\n{body_html}")
            
        # 2. Save metadata
        with open(os.path.join(package_path, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # 3. Create ZIP
        zip_file = os.path.join(self.output_dir, f"naver_{content_id}.zip")
        with zipfile.ZipFile(zip_file, 'w') as z:
            z.write(os.path.join(package_path, "content.html"), "content.html")
            z.write(os.path.join(package_path, "meta.json"), "meta.json")
            # Add images if provided
            for img in images:
                if os.path.exists(img):
                    z.write(img, os.path.join("images", os.path.basename(img)))
                    
        return zip_file
