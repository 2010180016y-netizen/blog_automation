import re
from typing import Dict, List

from .base import BaseRule


class EnBannedClaimsRule(BaseRule):
    def __init__(self, banned_words: List[str]):
        self.banned_words = banned_words

    def evaluate(self, content: str, context: Dict) -> Dict:
        found = [word for word in self.banned_words if word.lower() in content.lower()]
        if found:
            return {
                "status": "REJECT",
                "code": "EN_BANNED_CLAIM",
                "detail": f"Banned claims detected: {', '.join(found)}",
            }
        return None


class EnDisclosureRule(BaseRule):
    def __init__(self, disclosure_terms: List[str], affiliate_domains: List[str], link_window_chars: int = 220):
        self.disclosure_terms = [t.lower() for t in disclosure_terms]
        self.affiliate_domains = [d.lower() for d in affiliate_domains]
        self.link_window_chars = link_window_chars

    def _has_intro_disclosure(self, content: str) -> bool:
        intro = content.lower()[:240]
        return any(term in intro for term in self.disclosure_terms)

    def _iter_urls(self, content: str) -> List[re.Match]:
        pattern = re.compile(r"https?://[^\s)]+", re.IGNORECASE)
        return list(pattern.finditer(content))

    def _is_affiliate_url(self, url: str) -> bool:
        lower = url.lower()
        return any(domain in lower for domain in self.affiliate_domains) or any(
            token in lower for token in ["ref=", "aff", "affiliate", "utm_source=partner"]
        )

    def _has_disclosure_near(self, content: str, start_idx: int) -> bool:
        left = max(0, start_idx - self.link_window_chars)
        right = min(len(content), start_idx + self.link_window_chars)
        window = content.lower()[left:right]
        return any(term in window for term in self.disclosure_terms)

    def evaluate(self, content: str, context: Dict) -> Dict:
        disclosure_required = context.get("is_sponsored") or context.get("disclosure_required")

        if disclosure_required and not self._has_intro_disclosure(content):
            return {
                "status": "REJECT",
                "code": "EN_MISSING_DISCLOSURE",
                "detail": "Missing disclosure (sponsored/affiliate) in the intro.",
            }

        for match in self._iter_urls(content):
            url = match.group(0)
            if not self._is_affiliate_url(url):
                continue
            if not self._has_disclosure_near(content, match.start()):
                return {
                    "status": "REJECT",
                    "code": "EN_AFFILIATE_DISCLOSURE_MISSING",
                    "detail": "Affiliate links require clear and conspicuous disclosure nearby.",
                }

        return None
