from typing import Dict, Any, List
import re

class SEOValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def validate_technical_seo(self, html: str) -> Dict[str, Any]:
        """
        Checks for essential technical SEO tags in the rendered HTML.
        """
        checks = {
            "canonical": bool(re.search(r'<link rel="canonical"', html)),
            "og_tags": bool(re.search(r'property="og:', html)),
            "meta_description": bool(re.search(r'<meta name="description"', html)),
            "json_ld": bool(re.search(r'type="application/ld\+json"', html))
        }
        
        missing = [k for k, v in checks.items() if not v]
        
        return {
            "valid": len(missing) == 0,
            "checks": checks,
            "missing": missing
        }

    def validate_unique_pack(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures the 'Unique Pack' requirements are met to avoid 'scaled content abuse' flags.
        Requirements: FAQ, Tables, Checklists, or unique usage logs.
        """
        requirements = self.config.get("qa", {}).get("unique_pack", ["faq", "table", "checklist"])
        found = []
        
        if content_data.get("faq"): found.append("faq")
        if content_data.get("table"): found.append("table")
        if content_data.get("checklist"): found.append("checklist")
        if content_data.get("usage_log"): found.append("usage_log")
        
        missing = [r for r in requirements if r not in found]
        
        # We might require at least 2 unique elements
        is_valid = len(found) >= 2
        
        return {
            "valid": is_valid,
            "found": found,
            "missing": missing,
            "message": "Unique elements found: " + ", ".join(found) if is_valid else "Insufficient unique elements."
        }

    def check_indexing_basics(self, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks if robots.txt and sitemap.xml are configured in the site settings.
        """
        return {
            "robots_txt_enabled": site_config.get("robots_txt", False),
            "sitemap_enabled": site_config.get("sitemap", False),
            "search_console_verified": site_config.get("search_console_verified", False)
        }
