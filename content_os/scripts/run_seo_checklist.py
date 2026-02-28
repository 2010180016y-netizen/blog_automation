import argparse
import json
import os
import re
import sys
from urllib.parse import urljoin

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.validator import SEOValidator


HEAD_TIMEOUT = 10.0


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def fetch_text(url: str) -> str:
    with httpx.Client(timeout=HEAD_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def check_http_200(url: str) -> bool:
    try:
        with httpx.Client(timeout=HEAD_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url)
            return resp.status_code == 200
    except Exception:
        return False


def run_checklist(url: str = None, html_file: str = None, robots: bool = None, sitemap: bool = None, search_console: bool = None):
    validator = SEOValidator({"qa": {"unique_pack": ["faq", "table", "checklist"]}})

    if not url and not html_file:
        raise ValueError("Either --url or --html-file must be provided")

    report = {
        "target": url or html_file,
        "technical_seo": {},
        "indexing_basics": {},
        "result": "WARN",
    }

    # Determine HTML and site basics source
    if html_file:
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        site_config = {
            "robots_txt": bool(robots),
            "sitemap": bool(sitemap),
            "search_console_verified": bool(search_console),
        }
    else:
        html = fetch_text(url)
        base = url.rstrip("/") + "/"

        robots_ok = check_http_200(urljoin(base, "robots.txt")) if robots is None else bool(robots)
        sitemap_ok = check_http_200(urljoin(base, "sitemap.xml")) if sitemap is None else bool(sitemap)

        # No reliable external proof via plain HTTP for search-console verification in this script
        # so keep manual override support and default to False.
        sc_verified = bool(search_console) if search_console is not None else False

        site_config = {
            "robots_txt": robots_ok,
            "sitemap": sitemap_ok,
            "search_console_verified": sc_verified,
        }

    tech_report = validator.validate_technical_seo(html)
    basics_report = validator.check_indexing_basics(site_config)

    report["technical_seo"] = tech_report
    report["indexing_basics"] = basics_report

    warnings = []
    if not basics_report["robots_txt_enabled"]:
        warnings.append("robots.txt missing or unreachable")
    if not basics_report["sitemap_enabled"]:
        warnings.append("sitemap.xml missing or unreachable")
    if not basics_report["search_console_verified"]:
        warnings.append("search console verification not provided (manual check required)")
    if not tech_report["valid"]:
        warnings.append("missing technical tags: " + ", ".join(tech_report["missing"]))

    if tech_report["valid"] and basics_report["robots_txt_enabled"] and basics_report["sitemap_enabled"]:
        report["result"] = "PASS" if basics_report["search_console_verified"] else "WARN"
    else:
        report["result"] = "REJECT"

    report["warnings"] = warnings

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEO eligibility checklist")
    parser.add_argument("--url", help="Public page URL to check")
    parser.add_argument("--html-file", help="Local HTML file to check")
    parser.add_argument("--robots", help="Override robots result (true/false)")
    parser.add_argument("--sitemap", help="Override sitemap result (true/false)")
    parser.add_argument("--search-console", help="Set search console verified flag (true/false)")

    args = parser.parse_args()

    robots = parse_bool(args.robots) if args.robots is not None else None
    sitemap = parse_bool(args.sitemap) if args.sitemap is not None else None
    search_console = parse_bool(args.search_console) if args.search_console is not None else None

    run_checklist(
        url=args.url,
        html_file=args.html_file,
        robots=robots,
        sitemap=sitemap,
        search_console=search_console,
    )
