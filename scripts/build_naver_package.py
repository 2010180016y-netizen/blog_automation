#!/usr/bin/env python3
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_OS = os.path.join(ROOT, "content_os")
if CONTENT_OS not in sys.path:
    sys.path.insert(0, CONTENT_OS)

from app.publish.naver_package import NaverPackageGenerator


def parse_args():
    p = argparse.ArgumentParser(description="Build Naver blog publish package")
    p.add_argument("--content-id", required=True)
    p.add_argument("--product-id", required=True)
    p.add_argument("--source-type", required=True, choices=["MY_STORE", "AFFILIATE"])
    p.add_argument("--intent", required=True, choices=["info", "review", "compare", "story"])
    p.add_argument("--cta-link", required=True)
    p.add_argument("--output-root", default="out/naver_packages")
    p.add_argument("--ab", action="store_true", help="Create variant A/B packages for same content_id")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    gen = NaverPackageGenerator(output_root=args.output_root)
    if args.ab:
        result = gen.create_ab_variants(
            content_id=args.content_id,
            product_id=args.product_id,
            source_type=args.source_type,
            intent=args.intent,
            cta_link=args.cta_link,
        )
        ok = all(v.get("status") == "PASS" for v in result["variants"].values())
    else:
        result = gen.create_package(
            content_id=args.content_id,
            product_id=args.product_id,
            source_type=args.source_type,
            intent=args.intent,
            cta_link=args.cta_link,
        )
        ok = result.get("status") == "PASS"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
