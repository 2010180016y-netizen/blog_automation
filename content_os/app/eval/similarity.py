import re
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityEvaluator:
    def __init__(self, config: Dict):
        self.config = config
        self.threshold_warn = config.get('similarity', {}).get('thresholds', {}).get('warn', 0.80)
        self.threshold_reject = config.get('similarity', {}).get('thresholds', {}).get('reject', 0.88)
        self.ignore_sections = config.get('similarity', {}).get('ignore_sections', [])

    def split_paragraphs(self, text: str) -> List[str]:
        # Split by double newlines or headings
        paras = re.split(r'\n\s*\n|(?=^#+ )', text, flags=re.MULTILINE)
        # Filter out empty and ignored sections
        filtered = []
        for p in paras:
            p = p.strip()
            if not p: continue
            if any(section in p for section in self.ignore_sections):
                continue
            filtered.append(p)
        return filtered

    def calculate_similarity(self, target_paras: List[str], existing_paras: List[str]) -> List[Dict]:
        if not target_paras or not existing_paras:
            return []

        all_paras = target_paras + existing_paras
        vectorizer = TfidfVectorizer().fit(all_paras)
        
        target_vecs = vectorizer.transform(target_paras)
        existing_vecs = vectorizer.transform(existing_paras)
        
        similarities = cosine_similarity(target_vecs, existing_vecs)
        
        results = []
        for i, target_p in enumerate(target_paras):
            max_sim_idx = np.argmax(similarities[i])
            max_sim_score = similarities[i][max_sim_idx]
            
            if max_sim_score >= self.threshold_warn:
                results.append({
                    "target_paragraph": target_p[:120] + "...",
                    "existing_paragraph": existing_paras[max_sim_idx][:120] + "...",
                    "score": float(max_sim_score),
                    "status": "REJECT" if max_sim_score >= self.threshold_reject else "WARN"
                })
        
        return results

    def evaluate(self, content: str, existing_content_list: List[str]) -> Dict:
        target_paras = self.split_paragraphs(content)
        existing_paras = []
        for ec in existing_content_list:
            existing_paras.extend(self.split_paragraphs(ec))
            
        matches = self.calculate_similarity(target_paras, existing_paras)
        
        status = "PASS"
        if any(m["status"] == "REJECT" for m in matches):
            status = "REJECT"
        elif any(m["status"] == "WARN" for m in matches):
            status = "WARN"
            
        return {
            "status": status,
            "matches": matches,
            "summary": f"Found {len(matches)} highly similar paragraphs."
        }
