import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.internal_link_validator import validate_internal_links


def main():
    parser = argparse.ArgumentParser(description="Validate internal link graph with orphan detection and crawl simulation")
    parser.add_argument("--posts-json", required=True, help="JSON array of posts with slug/content/internal_links")
    parser.add_argument("--start-slug", action="append", default=[], help="Crawler seed slug (repeatable)")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-anchor-chars", type=int, default=2)
    args = parser.parse_args()

    with open(args.posts_json, "r", encoding="utf-8") as f:
        posts = json.load(f)

    report = validate_internal_links(
        posts,
        start_slugs=args.start_slug,
        max_depth=args.max_depth,
        min_anchor_chars=args.min_anchor_chars,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
