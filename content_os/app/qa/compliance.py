from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..eval.similarity import SimilarityEvaluator


REQUIRED_DISCLOSURE_TOKENS = ["광고", "제휴", "sponsored", "affiliate"]


def check_affiliate_disclosure_required(package: Dict) -> Dict:
    html = str(package.get("html") or "")
    has_disclosure = any(token in html.lower() for token in [t.lower() for t in REQUIRED_DISCLOSURE_TOKENS])

    if package.get("disclosure_required") and not has_disclosure:
        return {
            "status": "REJECT",
            "code": "AFFILIATE_DISCLOSURE_REQUIRED",
            "detail": "제휴/광고 표기가 누락되어 발행 불가",
        }
    return {"status": "PASS"}


def check_thin_content(package: Dict, min_text_chars: int = 250) -> Dict:
    html = str(package.get("html") or "")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < min_text_chars:
        return {
            "status": "REJECT",
            "code": "THIN_CONTENT",
            "detail": f"본문 텍스트 길이가 너무 짧습니다({len(text)}<{min_text_chars}).",
        }
    return {"status": "PASS", "chars": len(text)}


def check_similarity_content(
    package: Dict,
    existing_contents: Optional[List[str]] = None,
    warn_threshold: float = 0.80,
    reject_threshold: float = 0.88,
) -> Dict:
    existing_contents = existing_contents or []
    html = str(package.get("html") or "")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    if not text or not existing_contents:
        return {"status": "PASS", "matches": 0}

    evaluator = SimilarityEvaluator(
        {
            "similarity": {
                "thresholds": {"warn": warn_threshold, "reject": reject_threshold},
                "ignore_sections": ["가격", "배송", "옵션"],
            }
        }
    )
    result = evaluator.evaluate(text, existing_contents)

    if result["status"] == "REJECT":
        return {
            "status": "REJECT",
            "code": "SIMILARITY_REJECT",
            "detail": result.get("summary", "유사도 임계치 초과"),
            "matches": result.get("matches", []),
        }
    if result["status"] == "WARN":
        return {
            "status": "WARN",
            "code": "SIMILARITY_WARN",
            "detail": result.get("summary", "유사도 경고"),
            "matches": result.get("matches", []),
        }
    return {"status": "PASS", "matches": 0}


def check_unique_pack_required(unique_pack_result: Optional[Dict], require_unique_pack: bool = False) -> Dict:
    if not require_unique_pack:
        return {"status": "PASS", "mode": "OPTIONAL"}

    if not unique_pack_result:
        return {
            "status": "REJECT",
            "code": "UNIQUE_PACK_REQUIRED",
            "detail": "unique pack 결과가 없어 발행 불가",
        }

    if unique_pack_result.get("status") != "PASS":
        return {
            "status": "REJECT",
            "code": "UNIQUE_PACK_REJECT",
            "detail": str(unique_pack_result.get("reason") or "unique pack 검증 실패"),
        }

    return {"status": "PASS"}
