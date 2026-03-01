#!/usr/bin/env python3
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_OS = os.path.join(ROOT, "content_os")
if CONTENT_OS not in sys.path:
    sys.path.insert(0, CONTENT_OS)

from app.store.affiliate_import import import_affiliate_csv


def parse_args():
    p = argparse.ArgumentParser(description="Import AFFILIATE_SC links from CSV")
    p.add_argument("--csv", required=True, help="CSV path (exported by operator)")
    p.add_argument("--db", default=os.getenv("AFFILIATE_DB_PATH", os.path.join(CONTENT_OS, "blogs.db")))
    p.add_argument(
        "--intents",
        default="info,compare",
        help="comma-separated intents, e.g. info,compare,review",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    intents = [i.strip() for i in args.intents.split(",") if i.strip()]
    result = import_affiliate_csv(csv_path=args.csv, db_path=args.db, intents=intents)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
