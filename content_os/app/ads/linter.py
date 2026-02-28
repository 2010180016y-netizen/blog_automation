from __future__ import annotations

from typing import List, Dict, Any

from .dom_utils import DomUtils


class AdsLinter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules = config.get("ads_ux", {}).get("rules", {})
        self.min_dist = int(self.rules.get("min_distance_from_cta_px", 120))
        self.max_sibling_hops = max(1, self.min_dist // 60)
        self.forbidden_near = self.rules.get(
            "forbid_near_elements",
            ["button", "input", "select", "textarea", "video", "audio", "iframe", "[role='button']"],
        )

    def _is_forbidden(self, node: Any) -> bool:
        if node is None:
            return False
        node_classes = set(node.get("class", []))
        if "cta-button" in node_classes:
            return True
        if node.name in self.forbidden_near:
            return True
        return any(node.select(selector) for selector in self.forbidden_near)

    def _sibling_scan(self, ad: Any) -> List[Dict[str, Any]]:
        violations: List[Dict[str, Any]] = []
        ad_info = DomUtils.get_element_info(ad)

        for direction_name, next_fn in (("next", "find_next_sibling"), ("previous", "find_previous_sibling")):
            cursor = ad
            for hop in range(1, self.max_sibling_hops + 1):
                cursor = getattr(cursor, next_fn)()
                if cursor is None:
                    break
                if self._is_forbidden(cursor):
                    violations.append(
                        {
                            "level": "REJECT",
                            "message": f"Ad is too close ({hop} sibling hop/{direction_name}) to interactive element: <{cursor.name}>",
                            "ad": ad_info,
                            "offending_element": DomUtils.get_element_info(cursor),
                        }
                    )
                    break
        return violations

    def lint(self, html: str) -> Dict[str, Any]:
        """
        Performs static analysis on HTML to find UX violations in ad placement.
        Distance is approximated by sibling hops and interactive descendants.
        """
        violations: List[Dict[str, Any]] = []

        ads = DomUtils.find_elements(html, [".ad-unit", "ins.adsbygoogle", ".cos-ad"])

        for ad in ads:
            ad_info = DomUtils.get_element_info(ad)

            if self._is_forbidden(ad):
                violations.append(
                    {
                        "level": "REJECT",
                        "message": "Ad container contains an interactive control (potential accidental click risk).",
                        "ad": ad_info,
                        "offending_element": ad_info,
                    }
                )

            violations.extend(self._sibling_scan(ad))

        return {
            "status": "FAIL" if violations else "PASS",
            "violations": violations,
            "summary": f"Found {len(violations)} violations.",
            "rules_applied": {
                "min_distance_from_cta_px": self.min_dist,
                "max_sibling_hops": self.max_sibling_hops,
                "forbid_near_elements": self.forbidden_near,
            },
        }
