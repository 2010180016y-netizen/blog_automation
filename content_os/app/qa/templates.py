# Standard fix guides for common compliance and quality issues
FIX_GUIDES = {
    "KO_BANNED_CLAIM": {
        "title": "금지된 표현 수정",
        "action": "단정적인 표현(무조건, 완치 등)을 완화된 표현(~에 도움을 줄 수 있음)으로 수정하세요.",
        "priority": "HIGH"
    },
    "EN_BANNED_CLAIM": {
        "title": "Banned Claims Correction",
        "action": "Replace absolute claims (guaranteed, cure) with softer alternatives (may help, supports).",
        "priority": "HIGH"
    },
    "KO_MISSING_DISCLOSURE": {
        "title": "경제적 이해관계 표기 누락",
        "action": "본문 최상단에 [광고], [협찬], 또는 [제휴] 문구를 명시하세요.",
        "priority": "HIGH"
    },
    "EN_MISSING_DISCLOSURE": {
        "title": "Missing Disclosure",
        "action": "Add [Sponsored] or [Affiliate] disclosure at the beginning of the post.",
        "priority": "HIGH"
    },
    "KO_AFFILIATE_MISSING_DISCLOSURE": {
        "title": "제휴 표기 누락",
        "action": "제휴 글은 본문 최상단에 [광고]/[협찬]/[제휴] 문구를 반드시 삽입하세요.",
        "priority": "HIGH"
    },
    "EN_AFFILIATE_MISSING_DISCLOSURE": {
        "title": "Affiliate Disclosure Missing",
        "action": "Affiliate posts must include [Sponsored]/[Affiliate] disclosure at the top.",
        "priority": "HIGH"
    },
    "YMYL_MISSING_DISCLAIMER": {
        "title": "면책 문구 추가",
        "action": "본문 하단에 '본 내용은 전문가의 의견을 대신할 수 없습니다' 문구를 추가하세요.",
        "priority": "MEDIUM"
    },
    "SIMILARITY_REJECT": {
        "title": "유사도 위반 (복붙 의심)",
        "action": "해당 문단을 완전히 재작성하거나 나만의 구체적인 경험 사례를 추가하여 독창성을 확보하세요.",
        "priority": "HIGH"
    },
    "THIN_CONTENT": {
        "title": "분량 부족 및 구조 보강",
        "action": "H2 헤딩을 추가하고 각 섹션의 내용을 구체적인 수치나 사례로 보강하세요.",
        "priority": "MEDIUM"
    }
}

CHECKLIST_TEMPLATE = """
# 🛠 수정 지시서 (Fix Plan)
**상태: {status}**
**총 수정 항목: {total_items}개**

{items}

---
*지시서에 따라 수정한 후 다시 검수를 요청하세요.*
"""

ITEM_TEMPLATE = "- [{priority}] **{title}**: {action} (위치: {location})"
