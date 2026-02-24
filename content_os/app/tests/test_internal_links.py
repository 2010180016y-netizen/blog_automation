import unittest
from app.seo.cluster import TopicClusterer
from app.seo.internal_links import InternalLinkRecommender

class TestInternalLinks(unittest.TestCase):
    def setUp(self):
        self.posts = [
            {"id": 1, "slug": "post-1", "title": "아이폰 15 프로 리뷰", "summary": "애플의 최신 스마트폰 리뷰", "keywords": ["아이폰", "애플", "리뷰"]},
            {"id": 2, "slug": "post-2", "title": "갤럭시 S24 울트라 비교", "summary": "삼성 최신 폰과 아이폰 비교", "keywords": ["갤럭시", "삼성", "비교"]},
            {"id": 3, "slug": "post-3", "title": "스마트폰 구매 가이드", "summary": "2024년 최고의 폰 고르는 법", "keywords": ["스마트폰", "가이드"]},
            {"id": 4, "slug": "post-4", "title": "에어팟 프로 2 후기", "summary": "노이즈 캔슬링 이어폰 추천", "keywords": ["에어팟", "이어폰"]},
            {"id": 5, "slug": "post-5", "title": "맥북 에어 M3 성능", "summary": "가벼운 노트북의 끝판왕", "keywords": ["맥북", "노트북"]}
        ]
        self.clusterer = TopicClusterer()
        self.recommender = InternalLinkRecommender({"internal_links": {"max_links_per_post": 2}})

    def test_clustering_and_recommendation(self):
        clustered_posts = self.clusterer.cluster_posts(self.posts)
        
        # Check if neighbors are populated
        for post in clustered_posts:
            self.assertIn('cluster_neighbors', post)
            self.assertTrue(len(post['cluster_neighbors']) > 0)

        # Check recommendation for first post
        rec = self.recommender.recommend_links(clustered_posts[0])
        self.assertEqual(len(rec['recommendations']), 2)
        self.assertIn("markdown_snippet", rec)
        self.assertIn("post-1", clustered_posts[0]['slug'])
        
        # Ensure anchors are not just keywords
        for r in rec['recommendations']:
            self.assertTrue(any(phrase in r['anchor'] for phrase in ["보기", "확인하기", "가이드", "활용법", "좋은"]))

if __name__ == "__main__":
    unittest.main()
