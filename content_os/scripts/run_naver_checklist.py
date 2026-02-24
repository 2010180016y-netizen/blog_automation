import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.naver_validator import NaverValidator

def run_naver_checklist():
    validator = NaverValidator()
    
    # 1. Naver Blog Content Check
    blog_content = {
        "body": "최신 스마트폰 비교 리뷰입니다. 성능, 디자인, 가격 면에서 어떤 차이가 있는지 상세히 알아보겠습니다. 중복된 단어 없이 자연스러운 문장으로 구성되었습니다.",
        "links": ["https://smartstore.naver.com/example"],
        "images": [
            {"url": "img1.jpg", "is_unique": True},
            {"url": "img2.jpg", "is_unique": True},
            {"url": "img3.jpg", "is_unique": True}
        ],
        "has_comparison_table": True
    }
    
    blog_report = validator.validate_naver_blog_content(blog_content)
    
    # 2. Naver Web Search (WordPress) Check
    web_config = {
        "naver_verified": True,
        "sitemap_submitted": True,
        "robots_naver_allowed": True
    }
    web_report = validator.validate_naver_web_search(web_config)

    print("=== [2-B] Naver Exposure (Blog + Web) Checklist Report ===")
    
    print(f"\n[1] Naver Blog Quality (Anti-Spam):")
    if blog_report["valid"]:
        print("✅ PASSED: Content looks natural and high-quality.")
    else:
        print("❌ REJECTED: Quality issues found.")
        for v in blog_report["violations"]:
            print(f"   - {v}")
    print(f"   Score: {blog_report['score']}/100")

    print(f"\n[2] Naver Web Search (Search Advisor):")
    print(json.dumps(web_report, indent=2))

    if blog_report["valid"] and web_report["naver_search_advisor_verified"]:
        print("\n🎉 Overall Status: READY FOR NAVER EXPOSURE")
    else:
        print("\n⚠️  Overall Status: IMPROVEMENTS NEEDED")

if __name__ == "__main__":
    run_naver_checklist()
