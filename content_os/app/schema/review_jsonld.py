import json
from typing import Dict, Any

class ReviewJsonLdGenerator:
    def generate(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a Review JSON-LD object.
        """
        jsonld = {
            "@context": "https://schema.org/",
            "@type": "Review",
            "itemReviewed": {
                "@type": "Product",
                "name": review_data.get("product_name")
            },
            "author": {
                "@type": "Person",
                "name": review_data.get("author_name")
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": review_data.get("rating"),
                "bestRating": "5"
            },
            "reviewBody": review_data.get("body"),
            "publisher": {
                "@type": "Organization",
                "name": review_data.get("publisher_name", "Content OS")
            }
        }
        return {k: v for k, v in jsonld.items() if v is not None}
