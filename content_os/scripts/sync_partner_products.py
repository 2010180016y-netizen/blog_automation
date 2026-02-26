import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.partner_products import export_two_track_ssot, upsert_partner_products
from app.store.shopping_connect_ingest import (
    load_rows_from_csv,
    load_rows_from_google_sheet_csv,
    load_rows_from_json,
    normalize_rows,
    validate_shopping_connect_rows,
)


def main():
    parser = argparse.ArgumentParser(description="Sync Shopping Connect partner products and merge two-track SSOT")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--partner-json", default=None, help="JSON list of partner products")
    parser.add_argument("--partner-csv", default=None, help="CSV file of partner products")
    parser.add_argument("--sheet-csv-url", default=None, help="Published Google Sheet CSV URL")
    parser.add_argument("--check-link-live", action="store_true")
    parser.add_argument("--out-json", default=None, help="Optional merged SSOT json output")
    args = parser.parse_args()

    raw_rows = []
    if args.partner_json:
        raw_rows = load_rows_from_json(args.partner_json)
    elif args.partner_csv:
        raw_rows = load_rows_from_csv(args.partner_csv)
    elif args.sheet_csv_url:
        raw_rows = load_rows_from_google_sheet_csv(args.sheet_csv_url)
    else:
        raise ValueError("Provide one input: --partner-json or --partner-csv or --sheet-csv-url")

    products = normalize_rows(raw_rows)
    check = validate_shopping_connect_rows(products, check_link_live=args.check_link_live)
    if check["status"] == "REJECT":
        print(json.dumps({"partner_sync": {"upserted": 0, "validation": check}, "merged": None}, ensure_ascii=False, indent=2))
        return

    result = upsert_partner_products(args.db_path, products)

    merged = None
    if args.out_json:
        merged = export_two_track_ssot(args.db_path, args.out_json)

    print(json.dumps({"partner_sync": result, "input_validation": check, "merged": merged}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
