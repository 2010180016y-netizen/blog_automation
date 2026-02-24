from typing import List, Dict, Any
from .dom_utils import DomUtils

class AdsLinter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules = config.get("ads_ux", {}).get("rules", {})
        self.min_dist = self.rules.get("min_distance_from_cta_px", 120)
        self.forbidden_near = self.rules.get("forbid_near_elements", ["button", "input", "select"])

    def lint(self, html: str) -> Dict[str, Any]:
        """
        Performs static analysis on HTML to find UX violations in ad placement.
        Note: Since this is static analysis, 'distance' is approximated by DOM proximity.
        """
        violations = []
        
        # 1. Find all ads (assuming they have a specific class or tag)
        ads = DomUtils.find_elements(html, [".ad-unit", "ins.adsbygoogle", ".cos-ad"])
        
        # 2. Find interactive elements
        interactive_selectors = [f"{tag}" for tag in self.forbidden_near]
        interactive_selectors.append(".cta-button")
        interactive_elements = DomUtils.find_elements(html, interactive_selectors)

        for ad in ads:
            ad_info = DomUtils.get_element_info(ad)
            
            # Check immediate siblings for forbidden elements
            # This is a simplified proxy for 'distance' in static analysis
            siblings = ad.find_next_siblings() + ad.find_previous_siblings()
            for sibling in siblings:
                if sibling.name in self.forbidden_near or "cta-button" in sibling.get('class', []):
                    violations.append({
                        "level": "REJECT",
                        "message": f"Ad is immediately adjacent to interactive element: <{sibling.name}>",
                        "ad": ad_info,
                        "offending_element": DomUtils.get_element_info(sibling)
                    })

        return {
            "status": "FAIL" if violations else "PASS",
            "violations": violations,
            "summary": f"Found {len(violations)} violations."
        }
