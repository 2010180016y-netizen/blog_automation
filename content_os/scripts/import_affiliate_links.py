import argparse
import json
import os
import sys
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import (
    check_affiliate_disclosure_required,
    check_similarity_content,
    check_thin_content,
    check_unique_pack_required,
)
from app.store.shopping_connect_ingest import load_rows_from_csv, normalize_rows


def _load_json_list(path: Optional[str]) -> List[str]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [str(x) for x in data]
    return []


def _load_json_map(path: Optional[str]) -> Dict[str, Dict]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def run_import_and_package(
    db_path: str,
    csv_path: str,
    out_dir: str,
    min_text_chars: int = 250,
    existing_contents: Optional[List[str]] = None,
    require_unique_pack: bool = False,
    unique_pack_results_by_sku: Optional[Dict[str, Dict]] = None,
) -> dict:
    result = import_affiliate_links_from_csv(db_path, csv_path)
    if result.get("status") == "REJECT":
        return {"import": result, "queue_count": 0, "package_count": 0}

    rows = normalize_rows(load_rows_from_csv(csv_path))

    queue = create_content_queue_candidates(rows)
    os.makedirs(out_dir, exist_ok=True)

    existing_contents = existing_contents or []
    unique_pack_results_by_sku = unique_pack_results_by_sku or {}

    packages = []
    qa = []
    for row in rows:
        package = generate_naver_affiliate_package(row)
        disclosure_check = check_affiliate_disclosure_required(package)
        thin_content_check = check_thin_content(package, min_text_chars=min_text_chars)
        similarity_check = check_similarity_content(package, existing_contents=existing_contents)

        sku = str(row.get("partner_product_id") or row.get("sku") or "")
        unique_pack_check = check_unique_pack_required(
            unique_pack_results_by_sku.get(sku),
            require_unique_pack=require_unique_pack,
        )

        checks = [disclosure_check, thin_content_check, similarity_check, unique_pack_check]
        final_status = "PASS" if all(c.get("status") == "PASS" for c in checks) else "REJECT"

        packages.append(package)
        qa.append({"status": final_status, "checks": checks})

    with open(os.path.join(out_dir, "content_queue.json"), "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "packages.json"), "w", encoding="utf-8") as f:
        json.dump(packages, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "qa.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)

    return {"import": result, "queue_count": len(queue), "package_count": len(packages)}


def main():
    parser = argparse.ArgumentParser(description="Import Shopping Connect affiliate links and build Naver content packages")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--out-dir", default="./out/affiliate_packages")
    parser.add_argument("--existing-contents-path", help="JSON list file for similarity gate", default=None)
    parser.add_argument("--unique-pack-results-path", help="JSON map by sku for unique-pack gate", default=None)
    parser.add_argument("--require-unique-pack", action="store_true")
    args = parser.parse_args()

    summary = run_import_and_package(
        args.db_path,
        args.csv_path,
        args.out_dir,
        existing_contents=_load_json_list(args.existing_contents_path),
        require_unique_pack=args.require_unique_pack,
        unique_pack_results_by_sku=_load_json_map(args.unique_pack_results_path),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("import", {}).get("status") == "REJECT":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
