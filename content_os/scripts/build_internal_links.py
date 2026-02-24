import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.cluster import TopicClusterer
from app.seo.internal_links import InternalLinkRecommender

def build_internal_links():
    # Mock content list
    posts = [
        {"id": 1, "slug": "iphone-15-review", "title": "아이폰 15 리뷰", "summary": "애플 최신폰", "keywords": ["아이폰"]},
        {"id": 2, "slug": "galaxy-s24-review", "title": "갤럭시 S24 리뷰", "summary": "삼성 최신폰", "keywords": ["갤럭시"]},
        {"id": 3, "slug": "phone-comparison", "title": "스마트폰 비교", "summary": "아이폰 vs 갤럭시", "keywords": ["비교"]},
        {"id": 4, "slug": "macbook-m3", "title": "맥북 M3 리뷰", "summary": "신형 노트북", "keywords": ["맥북"]},
        {"id": 5, "slug": "ipad-pro", "title": "아이패드 프로", "summary": "태블릿 추천", "keywords": ["아이패드"]}
    ]

    config = {
        "internal_links": {
            "max_links_per_post": 3
        }
    }

    clusterer = TopicClusterer()
    recommender = InternalLinkRecommender(config)

    clustered = clusterer.cluster_posts(posts)
    
    results = []
    for post in clustered:
        results.append(recommender.recommend_links(post))

    output_path = "./out/internal_links.json"
    os.makedirs("./out", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Internal link recommendations built and saved to {output_path}")

if __name__ == "__main__":
    build_internal_links()
