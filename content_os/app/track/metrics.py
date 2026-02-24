import sqlite3
from typing import List, Dict

class MetricsAggregator:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path

    def get_summary_by_content(self) -> List[Dict]:
        query = """
            SELECT 
                content_id, 
                sku, 
                intent,
                COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as views,
                COUNT(CASE WHEN event_type IN ('cta_click', 'store_click') THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type = 'copy_coupon' THEN 1 END) as conversions
            FROM events
            GROUP BY content_id, sku, intent
        """
        
        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            for row in cursor:
                d = dict(row)
                # Calculate CTR
                d['ctr'] = (d['clicks'] / d['views'] * 100) if d['views'] > 0 else 0
                # Calculate Conversion Rate (approx)
                d['cvr'] = (d['conversions'] / d['views'] * 100) if d['views'] > 0 else 0
                results.append(d)
        return results
