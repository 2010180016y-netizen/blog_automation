import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.partner_products import export_two_track_ssot, upsert_partner_products


def main():
    parser = argparse.ArgumentParser(description="Sync partner (Shopping Connect) products and merge two-track SSOT")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--partner-json", required=True, help="JSON list of partner products")
    parser.add_argument("--out-json", default=None, help="Optional merged SSOT json output")
    args = parser.parse_args()

    with open(args.partner_json, "r", encoding="utf-8") as f:
        products = json.load(f)
    if not isinstance(products, list):
        raise ValueError("partner-json must be a JSON list")

    result = upsert_partner_products(args.db_path, products)

    merged = None
    if args.out_json:
        merged = export_two_track_ssot(args.db_path, args.out_json)

    print(json.dumps({"partner_sync": result, "merged": merged}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
