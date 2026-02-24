from typing import List, Dict, Any

class InsightExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources = config.get("store_improve", {}).get("sources", ["blog_faq", "comments", "cs_log"])

    def extract_top_questions(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extracts frequently asked questions from various sources.
        In a real scenario, this would use NLP/LLM to cluster and summarize.
        """
        questions = []
        for item in data:
            if item.get("type") in self.sources:
                questions.append({
                    "question": item.get("text"),
                    "source": item.get("type"),
                    "frequency": item.get("count", 1)
                })
        
        # Sort by frequency and return top 5
        return sorted(questions, key=lambda x: x["frequency"], reverse=True)[:5]

    def extract_warnings(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Extracts potential warnings or common complaints.
        """
        warnings = []
        for item in data:
            if "warning" in item.get("tags", []) or "complaint" in item.get("tags", []):
                warnings.append(item.get("text"))
        return list(set(warnings))
