import sqlite3
from typing import Dict, List


class MetricsAggregator:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path

    def get_summary_by_content(self) -> List[Dict]:
        query = """
            SELECT
                content_id,
                channel,
                sku,
                intent,
                COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as views,
                COUNT(CASE WHEN event_type IN ('cta_click', 'store_click', 'link_built') THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type IN ('copy_coupon', 'purchase') THEN 1 END) as conversions
            FROM events
            GROUP BY content_id, channel, sku, intent
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

    def get_channel_funnel(self) -> List[Dict]:
        query = """
            SELECT
                channel,
                COUNT(CASE WHEN event_type='page_view' THEN 1 END) AS views,
                COUNT(CASE WHEN event_type IN ('cta_click', 'store_click', 'link_built') THEN 1 END) AS clicks,
                COUNT(CASE WHEN event_type IN ('copy_coupon', 'purchase') THEN 1 END) AS conversions
            FROM events
            GROUP BY channel
            ORDER BY channel ASC
        """

        rows: List[Dict] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute(query):
                d = dict(row)
                d["click_through_rate"] = (d["clicks"] / d["views"] * 100) if d["views"] > 0 else 0
                d["conversion_rate"] = (d["conversions"] / d["views"] * 100) if d["views"] > 0 else 0
                rows.append(d)
        return rows

    def get_content_cohort_report(self) -> List[Dict]:
        query = """
            SELECT
                substr(timestamp, 1, 10) AS cohort_date,
                COUNT(DISTINCT content_id) AS contents,
                COUNT(*) AS events,
                COUNT(CASE WHEN event_type='page_view' THEN 1 END) AS views,
                COUNT(CASE WHEN event_type IN ('cta_click', 'store_click', 'link_built') THEN 1 END) AS clicks,
                COUNT(CASE WHEN event_type IN ('copy_coupon', 'purchase') THEN 1 END) AS conversions
            FROM events
            GROUP BY substr(timestamp, 1, 10)
            ORDER BY cohort_date ASC
        """

        rows: List[Dict] = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute(query):
                d = dict(row)
                d["ctr"] = (d["clicks"] / d["views"] * 100) if d["views"] > 0 else 0
                d["cvr"] = (d["conversions"] / d["views"] * 100) if d["views"] > 0 else 0
                rows.append(d)
        return rows

    def get_kpi_report(self) -> Dict:
        return {
            "summary_by_content": self.get_summary_by_content(),
            "channel_funnel": self.get_channel_funnel(),
            "content_cohorts": self.get_content_cohort_report(),
        }
