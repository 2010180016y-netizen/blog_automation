import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ads.linter import AdsLinter

def lint_html(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    config = {
        "ads_ux": {
            "rules": {
                "min_distance_from_cta_px": 120,
                "forbid_near_elements": ["button", "input", "select"]
            }
        }
    }

    linter = AdsLinter(config)
    report = linter.lint(html)

    print("--- Ads UX Lint Report ---")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Create a dummy file for testing if none provided
        dummy_path = "test_page.html"
        with open(dummy_path, "w") as f:
            f.write("<div><div class='ad-unit'>Ad</div><button>Buy</button></div>")
        lint_html(dummy_path)
    else:
        lint_html(sys.argv[1])
