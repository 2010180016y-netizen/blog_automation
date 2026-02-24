from datetime import datetime, timedelta
from typing import List, Dict, Any

class RefreshDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stale_days = config.get("refresh", {}).get("rules", {}).get("stale_days", 60)

    def detect_stale_content(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifies content older than stale_days.
        """
        stale_items = []
        now = datetime.now()
        
        for item in content_list:
            published_at = item.get("published_at")
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at)
            
            if now - published_at > timedelta(days=self.stale_days):
                stale_items.append({
                    "id": item["id"],
                    "reason": "STALE_CONTENT",
                    "days_old": (now - published_at).days
                })
        return stale_items

    def detect_product_changes(self, content_list: List[Dict[str, Any]], product_db: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifies content whose linked product info has changed.
        """
        changed_items = []
        for item in content_list:
            sku = item.get("sku")
            if not sku:
                continue
                
            current_product = product_db.get(sku)
            if not current_product:
                continue
            
            # Compare hash or modified_at
            last_known_hash = item.get("product_hash")
            current_hash = current_product.get("hash")
            
            if last_known_hash != current_hash:
                changed_items.append({
                    "id": item["id"],
                    "sku": sku,
                    "reason": "PRODUCT_INFO_CHANGED",
                    "changes": current_product.get("diff_summary", "정보 변경됨")
                })
        return changed_items
