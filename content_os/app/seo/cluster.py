from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import numpy as np

class TopicClusterer:
    def __init__(self, min_cluster_size: int = 4):
        self.min_cluster_size = min_cluster_size

    def cluster_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Groups posts based on content similarity (title + summary + keywords).
        """
        if not posts:
            return []

        texts = [f"{p['title']} {p.get('summary', '')} {' '.join(p.get('keywords', []))}" for p in posts]
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Simple clustering: for each post, find its most similar neighbors
        for i, post in enumerate(posts):
            # Get indices of posts sorted by similarity (descending)
            similar_indices = np.argsort(similarity_matrix[i])[::-1]
            # Exclude self (index i)
            similar_indices = [idx for idx in similar_indices if idx != i]
            
            post['cluster_neighbors'] = [
                {
                    "id": posts[idx].get("id"),
                    "slug": posts[idx].get("slug"),
                    "title": posts[idx].get("title"),
                    "score": float(similarity_matrix[i][idx])
                }
                for idx in similar_indices[:10] # Keep top 10 potential neighbors
            ]
            
        return posts
