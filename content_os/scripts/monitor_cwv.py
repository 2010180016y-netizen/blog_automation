import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.cwv_monitor import build_cwv_alert_report
from app.seo.feed_ops import send_ops_alert


def load_rows(path: str):
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def load_budgets(path: str):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def main():
    parser = argparse.ArgumentParser(description="Monitor Core Web Vitals with page-type budgets and regression alerts")
    parser.add_argument("--current-json", required=True, help="Current CWV rows JSON list")
    parser.add_argument("--previous-json", default=None, help="Previous CWV rows JSON list")
    parser.add_argument("--budget-json", default=None, help="Optional performance budget JSON by page_type")
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--email-to", default=None)
    args = parser.parse_args()

    current = load_rows(args.current_json)
    previous = load_rows(args.previous_json) if args.previous_json else []
    budgets = load_budgets(args.budget_json)

    report = build_cwv_alert_report(current_rows=current, previous_rows=previous, budgets=budgets)

    alert_result = None
    if report.get("overall") in ("WARN", "FAIL"):
        alert_result = send_ops_alert(report, webhook_url=args.webhook_url, email_to=args.email_to)

    print(
        json.dumps(
            {
                "report": report,
                "alert": alert_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
