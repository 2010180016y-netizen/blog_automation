import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.commerce_ssot import CommerceAPIConfig, NaverCommerceAPIClient, upsert_ssot_rows


def main():
    parser = argparse.ArgumentParser(description="Sync SmartStore products to SSOT table via Naver Commerce API")
    parser.add_argument("--base-url", required=True, help="Commerce API base url")
    parser.add_argument("--token", required=True, help="OAuth bearer token")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--client-id", default=None)
    parser.add_argument("--client-secret", default=None)
    parser.add_argument("--out-json", default=None, help="optional raw SSOT rows dump")
    args = parser.parse_args()

    client = NaverCommerceAPIClient(
        CommerceAPIConfig(
            base_url=args.base_url,
            token=args.token,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )
    )

    rows = client.fetch_ssot_rows(page=args.page, size=args.size)
    db_result = upsert_ssot_rows(args.db_path, rows)

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    print(json.dumps({"rows": len(rows), "db": db_result, "db_path": args.db_path}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
