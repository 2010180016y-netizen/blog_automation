import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.validator import SEOValidator

def run_essential_checklist():
    config = {
        "qa": {
            "unique_pack": ["faq", "table", "checklist"]
        }
    }
    
    validator = SEOValidator(config)
    
    # 1. Mock Site Basics
    site_basics = validator.check_indexing_basics({
        "robots_txt": True,
        "sitemap": True,
        "search_console_verified": False # Warning!
    })
    
    # 2. Mock Content Data (Unique Pack)
    content_data = {
        "title": "아이폰 15 프로 vs 갤럭시 S24 울트라",
        "faq": [{"q": "어떤 게 더 좋나요?", "a": "취향 차이입니다."}],
        "table": {"headers": ["기능", "아이폰", "갤럭시"], "rows": [["카메라", "좋음", "매우좋음"]]}
    }
    unique_report = validator.validate_unique_pack(content_data)
    
    # 3. Mock Rendered HTML (Technical SEO)
    html = """
    <html>
        <head>
            <link rel="canonical" href="https://example.com/vs">
            <meta name="description" content="아이폰과 갤럭시 비교">
            <meta property="og:title" content="아이폰 vs 갤럭시">
            <!-- Missing JSON-LD -->
        </head>
    </html>
    """
    tech_report = validator.validate_technical_seo(html)

    print("=== [2-A] WordPress SEO Essential Checklist Report ===")
    print(f"\n[1] Indexing Basics:")
    print(json.dumps(site_basics, indent=2))
    
    print(f"\n[2] Technical SEO (HTML Scan):")
    print(json.dumps(tech_report, indent=2))
    
    print(f"\n[3] Quality Control (Unique Pack):")
    print(json.dumps(unique_report, indent=2))

    if not site_basics["search_console_verified"] or not tech_report["valid"] or not unique_report["valid"]:
        print("\n⚠️  RESULT: REJECTED - Essential SEO settings missing or insufficient quality.")
    else:
        print("\n✅ RESULT: PASSED - Ready for scheduling.")

if __name__ == "__main__":
    run_essential_checklist()
