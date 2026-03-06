import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.feed_ops import (
    generate_rss,
    generate_sitemap,
    monitor_indexing_status,
    send_ops_alert,
)


def main():
    parser = argparse.ArgumentParser(description="Generate sitemap/RSS and monitor indexing status")
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--db-path", default="blogs.db")
    parser.add_argument("--out-dir", default="./out/feeds")
    parser.add_argument("--category", default=None)
    parser.add_argument("--google-status-json", default=None)
    parser.add_argument("--naver-status-json", default=None)
    parser.add_argument("--robots-txt", default=None)
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--email-to", default=None)

    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    sitemap_path = os.path.join(args.out_dir, "sitemap.xml")
    rss_path = os.path.join(args.out_dir, "rss.xml")

    sitemap_report = generate_sitemap(
        site_url=args.site_url,
        output_path=sitemap_path,
        db_path=args.db_path,
        category=args.category,
    )
    rss_report = generate_rss(
        site_url=args.site_url,
        output_path=rss_path,
        db_path=args.db_path,
        category=args.category,
    )

    monitor_report = monitor_indexing_status(
        google_status_json=args.google_status_json,
        naver_status_json=args.naver_status_json,
        robots_txt=args.robots_txt,
    )

    alert_report = send_ops_alert(
        report=monitor_report,
        webhook_url=args.webhook_url,
        email_to=args.email_to,
    )

    final = {
        "sitemap": sitemap_report,
        "rss": rss_report,
        "monitor": monitor_report,
        "alert": alert_report,
    }

    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
