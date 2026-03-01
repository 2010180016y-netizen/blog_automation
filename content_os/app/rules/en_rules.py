from .base import BaseRule
from typing import List, Dict

class EnBannedClaimsRule(BaseRule):
    def __init__(self, banned_words: List[str]):
        self.banned_words = banned_words

    def evaluate(self, content: str, context: Dict) -> Dict:
        found = [word for word in self.banned_words if word.lower() in content.lower()]
        if found:
            return {
                "status": "REJECT",
                "code": "EN_BANNED_CLAIM",
                "detail": f"Banned claims detected: {', '.join(found)}"
            }
        return None

class EnDisclosureRule(BaseRule):
    def evaluate(self, content: str, context: Dict) -> Dict:
        missing = not any(word in content.lower()[:200] for word in ["sponsored", "affiliate"])
        if not missing:
            return None

        if context.get("disclosure_required"):
            return {
                "status": "REJECT",
                "code": "EN_AFFILIATE_MISSING_DISCLOSURE",
                "detail": "Affiliate content requires disclosure (sponsored/affiliate) in the intro."
            }

        if context.get("is_sponsored"):
            return {
                "status": "REJECT",
                "code": "EN_MISSING_DISCLOSURE",
                "detail": "Missing disclosure (sponsored/affiliate) in the intro."
            }

        return None
