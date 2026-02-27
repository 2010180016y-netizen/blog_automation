import hashlib
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityEvaluator:
    def __init__(self, config: Dict):
        self.config = config
        sim_cfg = config.get("similarity", {})
        self.threshold_warn = sim_cfg.get("thresholds", {}).get("warn", 0.80)
        self.threshold_reject = sim_cfg.get("thresholds", {}).get("reject", 0.88)
        self.ignore_sections = sim_cfg.get("ignore_sections", [])
        self.max_existing_paragraphs = int(sim_cfg.get("max_existing_paragraphs", 2000))

        self._cache_key: Optional[str] = None
        self._cached_vectorizer: Optional[TfidfVectorizer] = None
        self._cached_existing_vecs = None
        self._cached_existing_paras: List[str] = []

    def split_paragraphs(self, text: str) -> List[str]:
        paras = re.split(r"\n\s*\n|(?=^#+ )", text, flags=re.MULTILINE)
        filtered = []
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if any(section in p for section in self.ignore_sections):
                continue
            filtered.append(p)
        return filtered

    def _make_existing_key(self, existing_paras: List[str]) -> str:
        joined = "\n".join(existing_paras)
        return hashlib.sha1(joined.encode("utf-8")).hexdigest()

    def _build_existing_matrix(self, target_paras: List[str], existing_paras: List[str]) -> Tuple[TfidfVectorizer, object]:
        existing_key = self._make_existing_key(existing_paras)

        if (
            self._cache_key == existing_key
            and self._cached_vectorizer is not None
            and self._cached_existing_vecs is not None
        ):
            return self._cached_vectorizer, self._cached_existing_vecs

        vectorizer = TfidfVectorizer().fit(existing_paras)
        existing_vecs = vectorizer.transform(existing_paras)

        self._cache_key = existing_key
        self._cached_vectorizer = vectorizer
        self._cached_existing_vecs = existing_vecs
        self._cached_existing_paras = existing_paras

        return vectorizer, existing_vecs

    def _trim_existing_paras(self, existing_paras: List[str]) -> List[str]:
        if len(existing_paras) <= self.max_existing_paragraphs:
            return existing_paras
        return existing_paras[-self.max_existing_paragraphs :]

    def calculate_similarity(self, target_paras: List[str], existing_paras: List[str]) -> List[Dict]:
        if not target_paras or not existing_paras:
            return []

        existing_paras = self._trim_existing_paras(existing_paras)
        vectorizer, existing_vecs = self._build_existing_matrix(target_paras, existing_paras)
        target_vecs = vectorizer.transform(target_paras)
        similarities = cosine_similarity(target_vecs, existing_vecs)

        results = []
        for i, target_p in enumerate(target_paras):
            max_sim_idx = np.argmax(similarities[i])
            max_sim_score = similarities[i][max_sim_idx]

            if max_sim_score >= self.threshold_warn:
                results.append(
                    {
                        "target_paragraph": target_p[:120] + "...",
                        "existing_paragraph": existing_paras[max_sim_idx][:120] + "...",
                        "score": float(max_sim_score),
                        "status": "REJECT" if max_sim_score >= self.threshold_reject else "WARN",
                    }
                )

        return results

    def evaluate(self, content: str, existing_content_list: List[str]) -> Dict:
        target_paras = self.split_paragraphs(content)
        existing_paras: List[str] = []
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
            "summary": f"Found {len(matches)} highly similar paragraphs.",
        }
