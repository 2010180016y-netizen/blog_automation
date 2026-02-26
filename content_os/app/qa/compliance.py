from __future__ import annotations

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
