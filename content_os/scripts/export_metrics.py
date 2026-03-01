import sys
import os
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.track.metrics import MetricsAggregator


def export_metrics(db_path: str = "blogs.db"):
    agg = MetricsAggregator(db_path=db_path)
    summary = agg.get_summary_by_content()

    output_dir = "./out"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "metrics.csv")

    if not summary:
        # still emit header-only csv for deterministic downstream handling
        headers = ["content_id", "sku", "intent", "views", "clicks", "conversions", "ctr", "cvr"]
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        print(f"No metrics rows. Header-only file exported to {output_file}")
        return output_file

    keys = ["content_id", "sku", "intent", "views", "clicks", "conversions", "ctr", "cvr"]
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(summary)

    print(f"Metrics exported to {output_file}")
    return output_file


if __name__ == "__main__":
    db_path = os.getenv("TRACKING_DB_PATH", "blogs.db")
    export_metrics(db_path=db_path)
