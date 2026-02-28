from __future__ import annotations

from typing import Dict, List, Optional


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def default_performance_budgets() -> Dict[str, Dict[str, float]]:
    return {
        "landing": {"lcp": 2.5, "inp": 200.0, "cls": 0.1, "ttfb": 0.8},
        "review": {"lcp": 2.8, "inp": 220.0, "cls": 0.1, "ttfb": 0.9},
        "comparison": {"lcp": 3.0, "inp": 250.0, "cls": 0.12, "ttfb": 1.0},
    }


def evaluate_cwv_by_page_type(
    rows: List[Dict],
    budgets: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, object]:
    budgets = budgets or default_performance_budgets()
    findings: List[Dict] = []

    for row in rows:
        page = row.get("page")
        page_type = str(row.get("page_type") or "landing").lower()
        metric_budget = budgets.get(page_type, budgets.get("landing", {}))

        lcp = _safe_float(row.get("lcp"))
        inp = _safe_float(row.get("inp"))
        cls = _safe_float(row.get("cls"))
        ttfb = _safe_float(row.get("ttfb"))

        breaches: List[Dict[str, float]] = []
        for metric, value in (("lcp", lcp), ("inp", inp), ("cls", cls), ("ttfb", ttfb)):
            budget = metric_budget.get(metric)
            if budget is None:
                continue
            if value > budget:
                breaches.append({"metric": metric, "value": value, "budget": budget, "delta": round(value - budget, 4)})

        severity = "PASS"
        if breaches:
            severity = "WARN"
        if len(breaches) >= 2 or any(b["metric"] in ("lcp", "inp") and b["delta"] > 0.6 for b in breaches):
            severity = "FAIL"

        findings.append(
            {
                "page": page,
                "page_type": page_type,
                "metrics": {"lcp": lcp, "inp": inp, "cls": cls, "ttfb": ttfb},
                "breaches": breaches,
                "severity": severity,
            }
        )

    overall = "PASS"
    if any(f["severity"] == "WARN" for f in findings):
        overall = "WARN"
    if any(f["severity"] == "FAIL" for f in findings):
        overall = "FAIL"

    return {"overall": overall, "budgets": budgets, "findings": findings}


def detect_regressions(current_rows: List[Dict], previous_rows: List[Dict], threshold: Optional[Dict[str, float]] = None) -> List[Dict]:
    threshold = threshold or {"lcp": 0.2, "inp": 20.0, "cls": 0.02, "ttfb": 0.1}

    prev_map = {str(r.get("page")): r for r in previous_rows if r.get("page")}
    regressions: List[Dict] = []

    for curr in current_rows:
        page = str(curr.get("page") or "")
        if not page or page not in prev_map:
            continue
        prev = prev_map[page]

        regressed: List[Dict] = []
        for metric in ("lcp", "inp", "cls", "ttfb"):
            c = _safe_float(curr.get(metric))
            p = _safe_float(prev.get(metric))
            delta = c - p
            if delta > threshold.get(metric, 0.0):
                regressed.append({"metric": metric, "current": c, "previous": p, "delta": round(delta, 4)})

        if regressed:
            regressions.append(
                {
                    "page": page,
                    "page_type": str(curr.get("page_type") or "landing").lower(),
                    "regressions": regressed,
                }
            )

    return regressions


def analyze_probable_causes(page_row: Dict) -> List[Dict]:
    causes: List[Dict] = []
    lcp = _safe_float(page_row.get("lcp"))
    cls = _safe_float(page_row.get("cls"))
    inp = _safe_float(page_row.get("inp"))

    image_kb = _safe_float(page_row.get("image_kb"))
    ad_script_kb = _safe_float(page_row.get("ad_script_kb"))
    plugin_script_kb = _safe_float(page_row.get("plugin_script_kb"))

    if image_kb > 900 or lcp > 2.8:
        causes.append({"component": "image", "severity": "HIGH", "detail": "Large/slow image payload likely impacting LCP."})
    if ad_script_kb > 250 or inp > 220:
        causes.append({"component": "ad_script", "severity": "HIGH", "detail": "Ad script execution may block main thread and degrade INP."})
    if plugin_script_kb > 300 or cls > 0.1:
        causes.append({"component": "plugin", "severity": "MEDIUM", "detail": "Plugin assets/layout shifts may contribute to CLS/TTFB issues."})

    if not causes:
        causes.append({"component": "unknown", "severity": "LOW", "detail": "No dominant source found; inspect RUM + waterfall traces."})

    return causes


def build_cwv_alert_report(
    current_rows: List[Dict],
    previous_rows: Optional[List[Dict]] = None,
    budgets: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, object]:
    previous_rows = previous_rows or []

    budget_report = evaluate_cwv_by_page_type(current_rows, budgets=budgets)
    regressions = detect_regressions(current_rows, previous_rows)

    current_map = {str(r.get("page")): r for r in current_rows if r.get("page")}
    alerts: List[Dict] = []

    for item in regressions:
        page = item["page"]
        causes = analyze_probable_causes(current_map.get(page, {}))
        alerts.append(
            {
                "page": page,
                "page_type": item.get("page_type"),
                "regressions": item["regressions"],
                "probable_causes": causes,
                "action": "OPTIMIZE_IMAGE_AD_PLUGIN_PAYLOAD",
            }
        )

    overall = budget_report["overall"]
    if alerts and overall == "PASS":
        overall = "WARN"

    return {
        "overall": overall,
        "budget_report": budget_report,
        "regressions": regressions,
        "alerts": alerts,
    }
