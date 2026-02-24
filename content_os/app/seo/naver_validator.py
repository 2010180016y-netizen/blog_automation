import re
from typing import Dict, Any, List

class NaverValidator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def validate_naver_blog_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates content against Naver Blog spam/quality policies.
        """
        text = content_data.get("body", "")
        links = content_data.get("links", [])
        images = content_data.get("images", [])
        
        # 1. Check for keyword stuffing (mechanical repetition)
        words = re.findall(r'\w+', text)
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        stuffing_detected = [w for w, c in word_counts.items() if c > 15 and len(w) > 1] # Simple threshold
        
        # 2. Check commercial balance (Link density)
        link_ratio = len(links) / (len(words) / 100) if words else 0
        is_too_commercial = link_ratio > 5 # More than 5 links per 100 words
        
        # 3. Unique Experience Check (Images/Tables)
        has_unique_images = len([img for img in images if img.get("is_unique")]) >= 3
        has_comparison = content_data.get("has_comparison_table", False)
        
        violations = []
        if stuffing_detected:
            violations.append(f"Keyword stuffing detected: {', '.join(stuffing_detected[:3])}")
        if is_too_commercial:
            violations.append(f"Too many links relative to text (Ratio: {link_ratio:.2f})")
        if not has_unique_images:
            violations.append("Insufficient unique images (Need at least 3 unique shots)")
        if not has_comparison:
            violations.append("Missing comparison table/experience log")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "score": 100 - (len(violations) * 20),
            "details": {
                "link_ratio": link_ratio,
                "unique_images_count": len(images)
            }
        }

    def validate_naver_web_search(self, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks settings for Naver Search Advisor (Web Search).
        """
        return {
            "naver_search_advisor_verified": site_config.get("naver_verified", False),
            "sitemap_submitted": site_config.get("sitemap_submitted", False),
            "robots_txt_naver_allowed": site_config.get("robots_naver_allowed", True),
            "recommendation": "Ensure sitemap.xml is submitted to Naver Search Advisor."
        }
