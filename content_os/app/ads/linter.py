from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .dom_utils import DomUtils


class AdsLinter:
    """Static ad UX linter to protect long-term ad policy safety.

    Because no runtime layout engine is available, we approximate physical distance
    by DOM proximity and sibling block density around ad slots.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules = config.get("ads_ux", {}).get("rules", {})

        # Keep px config for reporting intent even though this linter is static.
        self.min_dist_px = int(self.rules.get("min_distance_from_cta_px", 120))

        self.forbidden_near = self.rules.get("forbid_near_elements", ["button", "input", "select", "textarea"])
        self.cta_selectors = self.rules.get(
            "cta_selectors",
            [".cta-button", "a.cta", "a.buy-now", "button.cta-button"],
        )
        self.reject_if_gap_nodes_le = int(self.rules.get("reject_if_gap_nodes_le", 0))
        self.warn_if_gap_nodes_le = int(self.rules.get("warn_if_gap_nodes_le", 2))

    def _interactive_selector_list(self) -> List[str]:
        base = [tag for tag in self.forbidden_near]
        return base + list(self.cta_selectors)

    @staticmethod
    def _normalized_info(element: Any) -> Dict[str, Any]:
        info = DomUtils.get_element_info(element)
        info["path_hint"] = f"{element.name}#{element.get('id', '')}" if element else "unknown"
        return info

    @staticmethod
    def _same_parent_gap(ad: Any, target: Any) -> Optional[int]:
        if not ad or not target or ad.parent is None or target.parent is None:
            return None
        if ad.parent != target.parent:
            return None

        siblings = [c for c in ad.parent.children if getattr(c, "name", None)]
        try:
            ad_idx = siblings.index(ad)
            tgt_idx = siblings.index(target)
        except ValueError:
            return None
        return abs(tgt_idx - ad_idx) - 1

    def lint(self, html: str) -> Dict[str, Any]:
        """Run ad proximity checks and return PASS/WARN/REJECT report."""
        if not html or not str(html).strip():
            return {
                "status": "PASS",
                "violations": [],
                "summary": {
                    "reject_count": 0,
                    "warn_count": 0,
                    "checked_ad_units": 0,
                    "min_distance_from_cta_px": self.min_dist_px,
                },
            }

        soup = BeautifulSoup(html, "html.parser")
        ads = soup.select(".ad-unit, ins.adsbygoogle, .cos-ad")
        interactive_elements = soup.select(",".join(self._interactive_selector_list()))

        violations: List[Dict[str, Any]] = []
        for ad in ads:
            ad_info = self._normalized_info(ad)
            for target in interactive_elements:
                # ignore same node case
                if ad is target:
                    continue

                gap_nodes = self._same_parent_gap(ad, target)
                if gap_nodes is None:
                    continue

                level = None
                if gap_nodes <= self.reject_if_gap_nodes_le:
                    level = "REJECT"
                elif gap_nodes <= self.warn_if_gap_nodes_le:
                    level = "WARN"

                if level:
                    violations.append(
                        {
                            "level": level,
                            "message": (
                                f"Ad too close to interactive element in static DOM proximity check "
                                f"(gap_nodes={gap_nodes}, min_distance_from_cta_px={self.min_dist_px})."
                            ),
                            "ad": ad_info,
                            "offending_element": self._normalized_info(target),
                            "gap_nodes": gap_nodes,
                            "rule": {
                                "reject_if_gap_nodes_le": self.reject_if_gap_nodes_le,
                                "warn_if_gap_nodes_le": self.warn_if_gap_nodes_le,
                            },
                        }
                    )

        reject_count = len([v for v in violations if v["level"] == "REJECT"])
        warn_count = len([v for v in violations if v["level"] == "WARN"])

        status = "PASS"
        if reject_count > 0:
            status = "REJECT"
        elif warn_count > 0:
            status = "WARN"

        return {
            "status": status,
            "violations": violations,
            "summary": {
                "reject_count": reject_count,
                "warn_count": warn_count,
                "checked_ad_units": len(ads),
                "min_distance_from_cta_px": self.min_dist_px,
            },
        }
