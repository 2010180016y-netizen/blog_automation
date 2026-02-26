from __future__ import annotations

from typing import Dict, List


# P1 module: activate when own brandstore bizdata stats are available.
def summarize_brandstore_stats(rows: List[Dict]) -> Dict:
    total_impressions = 0
    total_clicks = 0
    total_orders = 0
    total_revenue = 0.0

    page_type_breakdown: Dict[str, Dict[str, float]] = {}

    for r in rows:
        page_type = str(r.get("page_type") or "unknown").lower()
        impressions = int(r.get("impressions") or 0)
        clicks = int(r.get("clicks") or 0)
        orders = int(r.get("orders") or 0)
        revenue = float(r.get("revenue") or 0.0)

        total_impressions += impressions
        total_clicks += clicks
        total_orders += orders
        total_revenue += revenue

        bucket = page_type_breakdown.setdefault(page_type, {"impressions": 0, "clicks": 0, "orders": 0, "revenue": 0.0})
        bucket["impressions"] += impressions
        bucket["clicks"] += clicks
        bucket["orders"] += orders
        bucket["revenue"] += revenue

    ctr = (total_clicks / total_impressions) if total_impressions else 0.0
    cvr = (total_orders / total_clicks) if total_clicks else 0.0

    return {
        "totals": {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "orders": total_orders,
            "revenue": round(total_revenue, 2),
            "ctr": round(ctr, 4),
            "cvr": round(cvr, 4),
        },
        "by_page_type": page_type_breakdown,
    }
