import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import check_affiliate_disclosure_required
from app.store.shopping_connect_ingest import load_rows_from_csv, normalize_rows


def main():
    parser = argparse.ArgumentParser(description="Import Shopping Connect affiliate links and build Naver content packages")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--out-dir", default="./out/affiliate_packages")
    args = parser.parse_args()

    result = import_affiliate_links_from_csv(args.db_path, args.csv_path)
    rows = normalize_rows(load_rows_from_csv(args.csv_path))

    queue = create_content_queue_candidates(rows)
    os.makedirs(args.out_dir, exist_ok=True)

    packages = []
    qa = []
    for row in rows:
        package = generate_naver_affiliate_package(row)
        check = check_affiliate_disclosure_required(package)
        packages.append(package)
        qa.append(check)

    with open(os.path.join(args.out_dir, "content_queue.json"), "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.out_dir, "packages.json"), "w", encoding="utf-8") as f:
        json.dump(packages, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.out_dir, "qa.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)

    print(json.dumps({"import": result, "queue_count": len(queue), "package_count": len(packages)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
