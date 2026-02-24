import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.insights import InsightExtractor
from app.store.update_pack import StoreUpdatePackGenerator

def build_store_pack(sku: str):
    config = {
        "store_improve": {
            "sources": ["blog_faq", "comments", "cs_log"],
            "pack_fields": ["top_questions", "recommended_answers", "warnings", "comparison_table"]
        }
    }

    # Mock data from various sources
    raw_data = [
        {"type": "blog_faq", "text": "이 제품 무선인가요?", "count": 15},
        {"type": "comments", "text": "소음이 좀 있네요", "tags": ["warning"], "count": 8},
        {"type": "cs_log", "text": "배터리 수명이 궁금해요", "count": 12},
        {"type": "comments", "text": "색상이 화면보다 밝아요", "tags": ["warning"], "count": 3}
    ]

    extractor = InsightExtractor(config)
    generator = StoreUpdatePackGenerator(config)

    insights = {
        "top_questions": extractor.extract_top_questions(raw_data),
        "warnings": extractor.extract_warnings(raw_data)
    }

    pack = generator.generate_pack(sku, insights)

    output_dir = "./out"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"store_pack_{sku}.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2, ensure_ascii=False)

    print(f"Store update pack for {sku} generated at {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_store_pack.py <sku>")
    else:
        build_store_pack(sys.argv[1])
