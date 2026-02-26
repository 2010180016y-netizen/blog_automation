import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import check_affiliate_disclosure_required, check_thin_content
from app.store.shopping_connect_ingest import load_rows_from_csv, normalize_rows


def run_import_and_package(db_path: str, csv_path: str, out_dir: str, min_text_chars: int = 250) -> dict:
    result = import_affiliate_links_from_csv(db_path, csv_path)
    if result.get("status") == "REJECT":
        return {"import": result, "queue_count": 0, "package_count": 0}

    rows = normalize_rows(load_rows_from_csv(csv_path))

    queue = create_content_queue_candidates(rows)
    os.makedirs(out_dir, exist_ok=True)

    packages = []
    qa = []
    for row in rows:
        package = generate_naver_affiliate_package(row)
        disclosure_check = check_affiliate_disclosure_required(package)
        thin_content_check = check_thin_content(package, min_text_chars=min_text_chars)

        checks = [disclosure_check, thin_content_check]
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
    args = parser.parse_args()

    summary = run_import_and_package(args.db_path, args.csv_path, args.out_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("import", {}).get("status") == "REJECT":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
