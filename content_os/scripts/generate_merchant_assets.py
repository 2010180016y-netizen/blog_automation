import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.merchant_center import (
    detect_product_changes,
    generate_merchant_center_feed,
    generate_product_merchant_jsonld,
    load_products_from_db,
)


def main():
    parser = argparse.ArgumentParser(description="Generate Merchant Center feed + Product JSON-LD from SSOT")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--out-dir", default="./out/merchant")
    parser.add_argument("--currency", default="KRW")
    parser.add_argument("--snapshot-path", default="./out/merchant/product_snapshot.json")
    args = parser.parse_args()

    products = load_products_from_db(args.db_path)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    feed_report = generate_merchant_center_feed(
        products=products,
        output_path=str(out_dir / "merchant_feed.xml"),
        site_url=args.site_url,
        currency=args.currency,
    )

    jsonld_dir = out_dir / "jsonld"
    jsonld_dir.mkdir(parents=True, exist_ok=True)
    jsonld_count = 0
    for p in products:
        sku = p.get("sku")
        if not sku:
            continue
        jsonld = generate_product_merchant_jsonld(p, site_url=args.site_url, currency=args.currency)
        (jsonld_dir / f"{sku}.json").write_text(json.dumps(jsonld, ensure_ascii=False, indent=2), encoding="utf-8")
        jsonld_count += 1

    change_report = detect_product_changes(products, snapshot_path=args.snapshot_path)

    result = {
        "products_total": len(products),
        "jsonld_generated": jsonld_count,
        "feed": feed_report,
        "changes": change_report,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
