import re
from typing import Dict, List

from .base import BaseRule


class KoBannedClaimsRule(BaseRule):
    def __init__(self, banned_words: List[str]):
        self.banned_words = banned_words

    def evaluate(self, content: str, context: Dict) -> Dict:
        found = [word for word in self.banned_words if word in content]
        if found:
            return {
                "status": "REJECT",
                "code": "KO_BANNED_CLAIM",
                "detail": f"금지된 표현 발견: {', '.join(found)}",
            }
        return None


class KoDisclosureRule(BaseRule):
    def __init__(self, disclosure_terms: List[str], affiliate_domains: List[str], link_window_chars: int = 180):
        self.disclosure_terms = disclosure_terms
        self.affiliate_domains = [d.lower() for d in affiliate_domains]
        self.link_window_chars = link_window_chars

    def _has_intro_disclosure(self, content: str) -> bool:
        intro = content[:200]
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
        window = content[left:right]
        return any(term in window for term in self.disclosure_terms)

    def evaluate(self, content: str, context: Dict) -> Dict:
        disclosure_required = context.get("is_sponsored") or context.get("disclosure_required")

        if disclosure_required and not self._has_intro_disclosure(content):
            return {
                "status": "REJECT",
                "code": "KO_MISSING_DISCLOSURE",
                "detail": "본문 상단에 광고/협찬/제휴 표기가 누락되었습니다.",
            }

        for match in self._iter_urls(content):
            url = match.group(0)
            if not self._is_affiliate_url(url):
                continue
            if not self._has_disclosure_near(content, match.start()):
                return {
                    "status": "REJECT",
                    "code": "KO_AFFILIATE_DISCLOSURE_MISSING",
                    "detail": "제휴 링크 근처에 명확한 경제적 이해관계 표기가 필요합니다.",
                }

        return None
