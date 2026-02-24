import sys
import os
import json
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline.unique_pack import UniquePackGenerator

def build_unique_pack(sku, content_id):
    # Mock config
    config = {
        "content_sources": {
            "image_assets_dir": "./assets/images",
            "video_assets_dir": "./assets/videos"
        },
        "unique_pack": {
            "required_per_post": {"min_images": 2, "min_unique_facts": 2},
            "outputs": {"package_dir": "./out/packages"}
        }
    }
    
    generator = UniquePackGenerator(config)
    result = generator.process(sku, content_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/build_unique_pack.py <sku> <content_id>")
    else:
        build_unique_pack(sys.argv[1], sys.argv[2])
