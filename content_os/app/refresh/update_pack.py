from typing import Dict, Any, List

class UpdatePackGenerator:
    def generate_pack(self, content_id: str, reason: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an update proposal package.
        """
        pack = {
            "content_id": content_id,
            "update_type": reason,
            "status": "PROPOSED",
            "proposed_changes": [],
            "change_log": f"Reason: {reason}"
        }

        if reason == "PRODUCT_INFO_CHANGED":
            pack["proposed_changes"].append({
                "location": "CTA_SECTION",
                "old_value": details.get("old_price"),
                "new_value": details.get("new_price"),
                "action": "Update price and availability"
            })
        elif reason == "STALE_CONTENT":
            pack["proposed_changes"].append({
                "location": "INTRO_SECTION",
                "action": "Refresh introduction with latest trends",
                "note": f"Content is {details.get('days_old')} days old."
            })

        return pack
