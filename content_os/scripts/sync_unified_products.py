import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.unified_products import sync_unified_products


def main():
    parser = argparse.ArgumentParser(description="Merge MY_STORE + AFFILIATE_SHOPPING_CONNECT into unified products table")
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--refresh-queue-path", default="./out/refresh_queue.json")
    args = parser.parse_args()

    result = sync_unified_products(args.db_path, refresh_queue_path=args.refresh_queue_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
