import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.store.brandstore_analytics import summarize_brandstore_stats


def main():
    parser = argparse.ArgumentParser(description="Summarize brandstore bizdata stats (P1)")
    parser.add_argument("--stats-json", required=True, help="JSON list rows with impressions/clicks/orders/revenue/page_type")
    args = parser.parse_args()

    with open(args.stats_json, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError("stats-json must be a list")

    report = summarize_brandstore_stats(rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
