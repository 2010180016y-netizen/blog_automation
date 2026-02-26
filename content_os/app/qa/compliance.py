from __future__ import annotations

import re
from typing import Dict


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
