import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingest.naver_commerce.client import NaverCommerceClient
from app.ingest.naver_commerce.sync import sync_my_store_products
from app.storage.repo import ProductRepo


def main():
    parser = argparse.ArgumentParser(description="Sync MY_STORE products via Naver Commerce API")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=100)
    args = parser.parse_args()

    client = NaverCommerceClient(
        base_url=args.base_url,
        client_id=args.client_id,
        client_secret=args.client_secret,
    )
    repo = ProductRepo(args.db_path)
    result = sync_my_store_products(client=client, repo=repo, page=args.page, size=args.size)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
