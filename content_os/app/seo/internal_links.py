from typing import Dict
import random


class InternalLinkRecommender:
    def __init__(self, config: Dict):
        self.config = config
        self.max_links = config.get("internal_links", {}).get("max_links_per_post", 5)

        self.anchor_templates = [
            "함께 읽어보면 좋은 {title}",
            "{title} 비교 기준 확인하기",
            "구매 전 {title} 체크리스트 보기",
            "{title} 관련 상세 가이드",
            "전문가가 제안하는 {title} 활용법",
        ]

    def _generate_anchor(self, target_title: str) -> str:
        template = random.choice(self.anchor_templates)
        return template.format(title=target_title)

    def recommend_links(self, post: Dict) -> Dict:
        neighbors = post.get("cluster_neighbors", [])
        selected_links = neighbors[: self.max_links]

        recommendations = []
        markdown_snippets = []

        for link in selected_links:
            anchor = self._generate_anchor(link["title"])
            url = f"/{link['slug']}"

            rec = {
                "slug": link["slug"],
                "title": link["title"],
                "anchor": anchor,
                "url": url,
                "score": link["score"],
            }
            recommendations.append(rec)
            markdown_snippets.append(f"[{anchor}]({url})")

        return {
            "post_id": post.get("id"),
            "recommendations": recommendations,
            "markdown_snippet": "\n".join(markdown_snippets),
        }

    def attach_recommendations(self, posts):
        for post in posts:
            result = self.recommend_links(post)
            post["internal_links"] = result["recommendations"]
        return posts
