import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.ops_dashboard import generate_ops_dashboard, load_json


def load_dict(path: str):
    if not path:
        return {}
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def main():
    parser = argparse.ArgumentParser(description="Generate Search Console/Naver ops dashboard report")
    parser.add_argument("--query-json", required=True, help="query-level rows (keyword/query, impressions, clicks, ctr)")
    parser.add_argument("--page-json", required=True, help="page-level rows (content_id/page, impressions, clicks, position)")
    parser.add_argument("--conversion-json", required=True, help="conversion rows (content_id, conversions)")
    parser.add_argument("--current-index-json", required=True, help="current index status dict {google:{errors..}, naver:{errors..}}")
    parser.add_argument("--previous-index-json", default=None, help="previous index status dict")

    args = parser.parse_args()

    report = generate_ops_dashboard(
        query_rows=load_json(args.query_json),
        page_rows=load_json(args.page_json),
        conversion_rows=load_json(args.conversion_json),
        current_index_status=load_dict(args.current_index_json),
        previous_index_status=load_dict(args.previous_index_json),
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
