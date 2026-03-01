from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ContentMeta:
    id: str
    title: str
    summary: str
    slug: str
    intent: str


class InternalLinkRecommendationEngine:
    """
    TF-IDF MVP recommender:
    - clusters by textual similarity (title+summary+intent)
    - returns related TOP-K (3~5 recommended by default)
    - uses behavior-oriented anchors to avoid keyword stuffing
    """

    def __init__(self, top_k: int = 3, max_k: int = 5, min_score: float = 0.05):
        self.top_k = min(max(3, top_k), max_k)
        self.max_k = max_k
        self.min_score = min_score
        self.anchor_templates = {
            "info": [
                "이 주제의 핵심 배경 먼저 보기: {title}",
                "문제 원인과 해결 흐름 이어서 보기: {title}",
            ],
            "review": [
                "실사용 관점의 체감 포인트 보기: {title}",
                "구매 전 체크할 경험 리뷰 보기: {title}",
            ],
            "compare": [
                "선택 기준 비교표 확인하기: {title}",
                "대안 비교 포인트 이어서 보기: {title}",
            ],
            "story": [
                "사용자 시나리오 이어보기: {title}",
                "적용 사례 흐름 확인하기: {title}",
            ],
            "default": ["관련 글 이어서 읽기: {title}"],
        }

    def _build_text(self, p: Dict) -> str:
        return f"{p.get('title','')} {p.get('summary','')} {p.get('intent','')}"

    def _anchor_for(self, intent: str, title: str, rank: int) -> str:
        templates = self.anchor_templates.get(intent, self.anchor_templates["default"])
        template = templates[rank % len(templates)]
        return template.format(title=title)

    def cluster(self, posts: List[Dict]) -> List[Dict]:
        if not posts:
            return []

        texts = [self._build_text(p) for p in posts]
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform(texts)
        sim = cosine_similarity(tfidf)

        enriched = []
        for i, post in enumerate(posts):
            row = sim[i]
            order = np.argsort(row)[::-1]
            neighbors = []
            for idx in order:
                if idx == i:
                    continue
                score = float(row[idx])
                if score < self.min_score:
                    continue
                target = posts[idx]
                neighbors.append(
                    {
                        "id": target.get("id"),
                        "slug": target.get("slug"),
                        "title": target.get("title"),
                        "intent": target.get("intent"),
                        "score": score,
                    }
                )
            enriched.append({**post, "cluster_neighbors": neighbors})
        return enriched

    def recommend(self, target_id: str, clustered_posts: List[Dict], top_k: Optional[int] = None) -> Dict:
        k = self.top_k if top_k is None else min(max(3, top_k), self.max_k)

        target = next((p for p in clustered_posts if str(p.get("id")) == str(target_id)), None)
        if not target:
            return {"target_id": target_id, "cluster_id": None, "recommendations": [], "html_snippet": ""}

        neighbors = target.get("cluster_neighbors", [])[:k]
        recs = []
        items_html = []
        for rank, n in enumerate(neighbors):
            anchor = self._anchor_for(n.get("intent", "default"), n["title"], rank)
            url = f"/{n['slug']}"
            recs.append(
                {
                    "id": n["id"],
                    "slug": n["slug"],
                    "title": n["title"],
                    "intent": n.get("intent"),
                    "score": n["score"],
                    "anchor": anchor,
                    "url": url,
                }
            )
            items_html.append(f"<li><a href='{url}'>{anchor}</a></li>")

        html_snippet = ""
        if recs:
            html_snippet = "<section class='next-reading'><h2>다음 읽을 글</h2><ul>" + "".join(items_html) + "</ul></section>"

        return {
            "target_id": target_id,
            "cluster_id": target.get("intent"),
            "recommendations": recs,
            "html_snippet": html_snippet,
        }
