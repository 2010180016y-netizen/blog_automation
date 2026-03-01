from .base import BaseRule
from typing import List, Dict

class KoBannedClaimsRule(BaseRule):
    def __init__(self, banned_words: List[str]):
        self.banned_words = banned_words

    def evaluate(self, content: str, context: Dict) -> Dict:
        found = [word for word in self.banned_words if word in content]
        if found:
            return {
                "status": "REJECT",
                "code": "KO_BANNED_CLAIM",
                "detail": f"금지된 표현 발견: {', '.join(found)}"
            }
        return None

class KoDisclosureRule(BaseRule):
    def evaluate(self, content: str, context: Dict) -> Dict:
        missing = not any(word in content[:100] for word in ["광고", "협찬", "제휴"])
        if not missing:
            return None

        if context.get("disclosure_required"):
            return {
                "status": "REJECT",
                "code": "KO_AFFILIATE_MISSING_DISCLOSURE",
                "detail": "제휴 콘텐츠는 본문 상단에 광고/협찬/제휴 표기가 필수입니다."
            }

        if context.get("is_sponsored"):
            return {
                "status": "REJECT",
                "code": "KO_MISSING_DISCLOSURE",
                "detail": "본문 상단에 광고/협찬/제휴 표기가 누락되었습니다."
            }

        return None
