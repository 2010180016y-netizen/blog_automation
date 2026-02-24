import sys
import os
import csv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.track.metrics import MetricsAggregator

def export_metrics():
    agg = MetricsAggregator()
    summary = agg.get_summary_by_content()
    
    output_dir = "./out"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "metrics.csv")
    
    if not summary:
        print("No metrics to export.")
        return

    keys = summary[0].keys()
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(summary)
        
    print(f"Metrics exported to {output_file}")

if __name__ == "__main__":
    export_metrics()
