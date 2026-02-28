from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _keyword_to_title(keyword: str) -> str:
    return f"{keyword}: 핵심 비교/선택 기준 총정리"


def _keyword_to_meta(keyword: str) -> str:
    return f"{keyword} 검색 의도에 맞춰 장단점, 선택 포인트, 추천 상황을 한눈에 정리했습니다."


def detect_low_ctr_keywords(
    query_rows: List[Dict],
    min_impressions: int = 300,
    ctr_threshold: float = 0.02,
) -> List[Dict]:
    findings: List[Dict] = []
    for row in query_rows:
        keyword = (row.get("keyword") or row.get("query") or "").strip()
        if not keyword:
            continue

        impressions = _safe_int(row.get("impressions"))
        clicks = _safe_int(row.get("clicks"))
        ctr = _safe_float(row.get("ctr"), (clicks / impressions) if impressions else 0.0)

        if impressions >= min_impressions and ctr < ctr_threshold:
            findings.append(
                {
                    "keyword": keyword,
                    "page": row.get("page"),
                    "impressions": impressions,
                    "clicks": clicks,
                    "ctr": ctr,
                    "action": "TITLE_META_AB_TEST",
                    "title_candidates": [
                        _keyword_to_title(keyword),
                        f"{keyword} 실사용 기준으로 고르는 법",
                    ],
                    "meta_candidates": [
                        _keyword_to_meta(keyword),
                        f"{keyword} 관련 핵심 질문과 실제 선택 기준을 간결하게 정리했습니다.",
                    ],
                }
            )
    return findings


def detect_indexing_error_increase(
    current_status: Dict,
    previous_status: Optional[Dict] = None,
    delta_threshold: int = 1,
) -> List[Dict]:
    previous_status = previous_status or {}
    alerts: List[Dict] = []

    for source in ("google", "naver"):
        curr = _safe_int(current_status.get(source, {}).get("errors"))
        prev = _safe_int(previous_status.get(source, {}).get("errors"))
        delta = curr - prev

        if delta >= delta_threshold:
            alerts.append(
                {
                    "source": source,
                    "current_errors": curr,
                    "previous_errors": prev,
                    "delta": delta,
                    "severity": "HIGH" if delta >= 5 else "MEDIUM",
                    "action": "CHECK_SITEMAP_AND_CRAWL_ERRORS",
                }
            )

    return alerts


def flag_high_rank_low_conversion(
    page_rows: List[Dict],
    conversion_rows: List[Dict],
    rank_threshold: float = 5.0,
    min_clicks: int = 50,
    max_conversion_rate: float = 0.01,
) -> List[Dict]:
    conversion_map = {
        str(r.get("content_id")): _safe_int(r.get("conversions"))
        for r in conversion_rows
    }

    flagged: List[Dict] = []
    for row in page_rows:
        content_id = str(row.get("content_id") or row.get("id") or "")
        if not content_id:
            continue

        avg_position = _safe_float(row.get("avg_position") or row.get("position"), 999)
        clicks = _safe_int(row.get("clicks"))
        conversions = conversion_map.get(content_id, 0)
        conv_rate = (conversions / clicks) if clicks > 0 else 0.0

        if avg_position <= rank_threshold and clicks >= min_clicks and conv_rate <= max_conversion_rate:
            flagged.append(
                {
                    "content_id": content_id,
                    "page": row.get("page"),
                    "avg_position": avg_position,
                    "clicks": clicks,
                    "conversions": conversions,
                    "conversion_rate": conv_rate,
                    "action": "REVIEW_CTA_AND_PRODUCT_MATCH",
                }
            )

    return flagged


def build_refresh_priority(
    page_rows: List[Dict],
    conversion_rows: List[Dict],
) -> List[Dict]:
    conversion_map = {
        str(r.get("content_id")): _safe_int(r.get("conversions"))
        for r in conversion_rows
    }

    ranked: List[Dict] = []
    for row in page_rows:
        content_id = str(row.get("content_id") or row.get("id") or "")
        if not content_id:
            continue

        impressions = _safe_int(row.get("impressions"))
        clicks = _safe_int(row.get("clicks"))
        ctr = _safe_float(row.get("ctr"), (clicks / impressions) if impressions else 0.0)
        position = _safe_float(row.get("avg_position") or row.get("position"), 100.0)
        conversions = conversion_map.get(content_id, 0)

        # Higher score => higher refresh priority
        score = (
            impressions * 0.01
            + max(0.0, (0.03 - ctr)) * 800
            + max(0.0, (10.0 - position)) * 5
            - conversions * 2
        )

        ranked.append(
            {
                "content_id": content_id,
                "page": row.get("page"),
                "score": round(score, 2),
                "impressions": impressions,
                "ctr": round(ctr, 4),
                "avg_position": round(position, 2),
                "conversions": conversions,
            }
        )

    return sorted(ranked, key=lambda x: x["score"], reverse=True)


def generate_ops_dashboard(
    query_rows: List[Dict],
    page_rows: List[Dict],
    conversion_rows: List[Dict],
    current_index_status: Dict,
    previous_index_status: Optional[Dict] = None,
) -> Dict:
    low_ctr = detect_low_ctr_keywords(query_rows)
    index_alerts = detect_indexing_error_increase(current_index_status, previous_index_status)
    low_conv = flag_high_rank_low_conversion(page_rows, conversion_rows)
    refresh_priority = build_refresh_priority(page_rows, conversion_rows)

    overall = "PASS"
    if index_alerts:
        overall = "WARN"
    if any(a.get("severity") == "HIGH" for a in index_alerts):
        overall = "FAIL"

    return {
        "overall": overall,
        "low_ctr_keywords": low_ctr,
        "indexing_alerts": index_alerts,
        "high_rank_low_conversion": low_conv,
        "refresh_priority": refresh_priority[:20],
    }


def load_json(path: Optional[str]) -> List[Dict]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []
