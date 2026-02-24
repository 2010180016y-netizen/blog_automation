import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage.repo import ContentRepo
from app.eval.similarity import SimilarityEvaluator

def check_one(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    repo = ContentRepo()
    config = {
        "similarity": {
            "thresholds": {"warn": 0.80, "reject": 0.88},
            "ignore_sections": ["가격", "배송", "옵션"]
        }
    }
    evaluator = SimilarityEvaluator(config)
    
    existing_entries = repo.get_all_entries()
    existing_contents = [e.content for e in existing_entries]
    
    result = evaluator.evaluate(content, existing_contents)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_one.py <file_path>")
    else:
        check_one(sys.argv[1])
