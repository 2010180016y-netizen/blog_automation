import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.refresh.detector import RefreshDetector
from app.refresh.update_pack import UpdatePackGenerator

def run_refresh():
    config = {"refresh": {"rules": {"stale_days": 60}}}
    
    # Mock data
    content_list = [
        {"id": "POST001", "published_at": "2023-12-01T00:00:00", "sku": "SKU001", "product_hash": "h1"},
        {"id": "POST002", "published_at": datetime.now().isoformat(), "sku": "SKU002", "product_hash": "h2"}
    ]
    
    product_db = {
        "SKU001": {"hash": "h1"}, # No change
        "SKU002": {"hash": "h2_new", "diff_summary": "Price updated to 120,000"} # Changed
    }

    detector = RefreshDetector(config)
    generator = UpdatePackGenerator()

    stale = detector.detect_stale_content(content_list)
    changed = detector.detect_product_changes(content_list, product_db)

    all_triggers = stale + changed
    packs = []

    for trigger in all_triggers:
        pack = generator.generate_pack(trigger["id"], trigger["reason"], trigger)
        packs.append(pack)

    output_path = "./out/refresh_packs.json"
    os.makedirs("./out", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(packs, f, indent=2, ensure_ascii=False)

    print(f"Refresh check complete. {len(packs)} update packs generated in {output_path}")

if __name__ == "__main__":
    run_refresh()
