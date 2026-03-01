import sqlite3
from typing import Dict, List


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
                COUNT(CASE WHEN event_type = 'store_click' THEN 1 END) as conversions
            FROM events
            GROUP BY content_id, sku, intent
        """

        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            for row in cursor:
                d = dict(row)
                d["ctr"] = (d["clicks"] / d["views"] * 100) if d["views"] > 0 else 0
                d["cvr"] = (d["conversions"] / d["views"] * 100) if d["views"] > 0 else 0
                results.append(d)
        return results

    def get_variant_ctr(self, content_id: str) -> List[Dict]:
        """A/B variant CTR 집계. variant는 events.metadata.variant에서 추출."""
        query = """
            SELECT
                COALESCE(json_extract(metadata, '$.variant'), 'unknown') as variant,
                COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as views,
                COUNT(CASE WHEN event_type IN ('cta_click', 'store_click') THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type = 'store_click' THEN 1 END) as store_clicks,
                COUNT(CASE WHEN event_type = 'cta_click' THEN 1 END) as cta_clicks
            FROM events
            WHERE content_id = ?
            GROUP BY COALESCE(json_extract(metadata, '$.variant'), 'unknown')
            ORDER BY variant
        """

        rows: List[Dict] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute(query, (content_id,)):
                d = dict(row)
                d["ctr"] = (d["clicks"] / d["views"] * 100) if d["views"] else 0
                rows.append(d)
        return rows

    def pick_winner_variant(self, content_id: str) -> Dict:
        variants = self.get_variant_ctr(content_id)
        if not variants:
            return {"content_id": content_id, "winner": None, "reason": "no_data", "variants": []}

        # 승자 기준: store_click 우선, 동률이면 cta_click, 이후 CTR
        winner = sorted(variants, key=lambda v: (v["store_clicks"], v["cta_clicks"], v["ctr"]), reverse=True)[0]
        return {
            "content_id": content_id,
            "winner": winner["variant"],
            "reason": "max_store_click_then_cta_click_then_ctr",
            "variants": variants,
        }
