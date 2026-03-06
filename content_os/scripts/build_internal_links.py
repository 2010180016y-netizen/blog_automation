import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seo.cluster import TopicClusterer
from app.seo.internal_links import InternalLinkRecommender
from app.seo.internal_link_validator import validate_internal_links


def build_internal_links():
    posts = [
        {"id": 1, "slug": "iphone-15-review", "title": "아이폰 15 리뷰", "summary": "애플 최신폰", "keywords": ["아이폰"]},
        {"id": 2, "slug": "galaxy-s24-review", "title": "갤럭시 S24 리뷰", "summary": "삼성 최신폰", "keywords": ["갤럭시"]},
        {"id": 3, "slug": "phone-comparison", "title": "스마트폰 비교", "summary": "아이폰 vs 갤럭시", "keywords": ["비교"]},
        {"id": 4, "slug": "macbook-m3", "title": "맥북 M3 리뷰", "summary": "신형 노트북", "keywords": ["맥북"]},
        {"id": 5, "slug": "ipad-pro", "title": "아이패드 프로", "summary": "태블릿 추천", "keywords": ["아이패드"]},
    ]

    config = {"internal_links": {"max_links_per_post": 3}}

    clusterer = TopicClusterer()
    recommender = InternalLinkRecommender(config)

    clustered = clusterer.cluster_posts(posts)
    enriched = recommender.attach_recommendations(clustered)

    results = []
    for post in enriched:
        rec = recommender.recommend_links(post)
        post["content"] = rec["markdown_snippet"]
        results.append(rec)

    validation = validate_internal_links(enriched, start_slugs=[enriched[0]["slug"]], max_depth=3)

    os.makedirs("./out", exist_ok=True)
    with open("./out/internal_links.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open("./out/internal_link_posts.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    with open("./out/internal_links_validation.json", "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2, ensure_ascii=False)

    print("Internal link recommendations saved to ./out/internal_links.json")
    print("Internal link posts saved to ./out/internal_link_posts.json")
    print("Internal link validation saved to ./out/internal_links_validation.json")


if __name__ == "__main__":
    build_internal_links()
