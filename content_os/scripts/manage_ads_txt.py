import argparse
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ads.ads_txt import (
    fetch_ads_txt,
    generate_ads_txt,
    load_sellers_from_json,
    validate_ads_txt_content,
    write_ads_txt,
)


def main():
    parser = argparse.ArgumentParser(description="Generate/validate/deploy ads.txt")
    parser.add_argument("--records-json", required=True, help="JSON file with seller records")
    parser.add_argument("--output-path", default="./out/ads/ads.txt")
    parser.add_argument("--expected-domain", action="append", default=[])
    parser.add_argument("--validate-url", help="Optional existing ads.txt URL to validate")
    args = parser.parse_args()

    sellers = load_sellers_from_json(args.records_json)
    content = generate_ads_txt(sellers)
    output = write_ads_txt(content, args.output_path)

    generated_validation = validate_ads_txt_content(content, expected_domains=args.expected_domain)

    remote_validation = None
    if args.validate_url:
        remote_content = fetch_ads_txt(args.validate_url)
        remote_validation = validate_ads_txt_content(remote_content, expected_domains=args.expected_domain)

    print(
        json.dumps(
            {
                "generated_file": output,
                "generated": generated_validation,
                "remote": remote_validation,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
