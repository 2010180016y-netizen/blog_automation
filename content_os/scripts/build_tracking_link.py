import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.track.event_collector import EventCollector
from app.track.link_builder import LinkBuilder


def main() -> int:
    parser = argparse.ArgumentParser(description="Build tracking link and record link_built event")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--sku", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--db-path", default="blogs.db")
    args = parser.parse_args()

    builder = LinkBuilder(config={})
    tracking_url = builder.build_tracking_link(
        args.base_url,
        channel=args.channel,
        content_id=args.content_id,
        sku=args.sku,
        intent=args.intent,
    )

    collector = EventCollector(db_path=args.db_path)
    collector.collect(
        event_type="link_built",
        channel=args.channel,
        content_id=args.content_id,
        sku=args.sku,
        intent=args.intent,
        metadata={"base_url": args.base_url, "tracking_url": tracking_url},
    )

    print(json.dumps({"status": "ok", "tracking_url": tracking_url}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
