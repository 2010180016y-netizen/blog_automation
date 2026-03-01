from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..eval.compliance import ComplianceEvaluator
from ..eval.similarity import SimilarityEvaluator
from .fixplan import FixPlanGenerator


@dataclass
class QAGateInput:
    content: str
    language: str = "ko"
    category: str = "General"
    source_type: str = "MY_STORE"  # MY_STORE / AFFILIATE
    is_sponsored: bool = False
    existing_contents: Optional[List[str]] = None
    content_data: Optional[Dict[str, Any]] = None


class QAGate:
    """
    All-in-one QA gate.

    checks:
    - compliance: banned claims / disclosure / YMYL
    - similarity: paragraph-level TF-IDF similarity
    - thin-content: required sections/faq/example/caution minima
    - unique-pack: min images + min unique facts
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.compliance = ComplianceEvaluator()
        self.similarity = SimilarityEvaluator(
            self.config.get(
                "similarity",
                {
                    "similarity": {
                        "thresholds": {"warn": 0.8, "reject": 0.88},
                        "ignore_sections": [],
                    }
                },
            )
        )
        self.fixplan = FixPlanGenerator(self.config)

    def _check_thin_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        required_sections = self.config.get(
            "qa",
            {},
        ).get("required_sections", ["사용법", "공식(근거)", "예시", "추천 대상 / 비추천 대상", "구매 전 체크리스트", "경쟁/대체 옵션 비교표", "FAQ", "주의사항", "엣지케이스"])
        section_titles = content_data.get("section_titles", [])

        missing_sections = [s for s in required_sections if s not in section_titles]
        faq_count = int(content_data.get("faq_count", 0))
        example_count = int(content_data.get("example_count", 0))
        caution_count = int(content_data.get("caution_count", 0))

        violations = []
        if missing_sections:
            violations.append(
                {
                    "code": "THIN_CONTENT",
                    "detail": f"필수 섹션 누락: {', '.join(missing_sections)}",
                    "location": "본문 구조",
                }
            )
        if faq_count < 6:
            violations.append({"code": "THIN_CONTENT", "detail": "FAQ 최소 6개 필요", "location": "FAQ"})
        if example_count < 1:
            violations.append({"code": "THIN_CONTENT", "detail": "예시 최소 1개 필요", "location": "예시"})
        if caution_count < 1:
            violations.append({"code": "THIN_CONTENT", "detail": "주의사항 최소 1개 필요", "location": "주의사항"})

        return {
            "status": "REJECT" if violations else "PASS",
            "fail": violations,
            "warn": [],
            "meta": {
                "missing_sections": missing_sections,
                "faq_count": faq_count,
                "example_count": example_count,
                "caution_count": caution_count,
            },
        }

    def _check_unique_pack(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        min_images = int(self.config.get("qa", {}).get("unique_pack", {}).get("min_images", 2))
        min_facts = int(self.config.get("qa", {}).get("unique_pack", {}).get("min_facts", 2))

        image_count = int(content_data.get("image_count", 0))
        unique_fact_count = int(content_data.get("unique_fact_count", 0))

        fails = []
        if image_count < min_images:
            fails.append(
                {
                    "code": "UNIQUE_PACK_INSUFFICIENT_IMAGES",
                    "detail": f"이미지 부족: {image_count}/{min_images}",
                    "location": "images",
                }
            )
        if unique_fact_count < min_facts:
            fails.append(
                {
                    "code": "UNIQUE_PACK_INSUFFICIENT_FACTS",
                    "detail": f"고유 사실 부족: {unique_fact_count}/{min_facts}",
                    "location": "unique_pack",
                }
            )

        return {
            "status": "REJECT" if fails else "PASS",
            "fail": fails,
            "warn": [],
            "meta": {
                "image_count": image_count,
                "unique_fact_count": unique_fact_count,
                "min_images": min_images,
                "min_facts": min_facts,
            },
        }

    def evaluate(self, qa_input: QAGateInput) -> Dict[str, Any]:
        content_data = qa_input.content_data or {}
        existing_contents = qa_input.existing_contents or []

        disclosure_required = qa_input.source_type == "AFFILIATE"

        comp_req = {
            "content": qa_input.content,
            "language": qa_input.language,
            "category": qa_input.category,
            "is_sponsored": qa_input.is_sponsored,
            "disclosure_required": disclosure_required,
        }

        from ..schemas import ComplianceRequest

        comp_res = self.compliance.evaluate(ComplianceRequest(**comp_req))
        sim_res = self.similarity.evaluate(qa_input.content, existing_contents)
        thin_res = self._check_thin_content(content_data)
        unique_res = self._check_unique_pack(content_data)

        fails: List[Dict[str, Any]] = []
        warns: List[Dict[str, Any]] = []

        fails.extend(comp_res.fail)
        warns.extend(comp_res.warn)

        for m in sim_res.get("matches", []):
            code = "SIMILARITY_REJECT" if m["status"] == "REJECT" else "SIMILARITY_WARN"
            item = {
                "code": code,
                "detail": f"유사도 {m['score']:.2f}: {m['target_paragraph']}",
                "location": "paragraph",
            }
            if m["status"] == "REJECT":
                fails.append(item)
            else:
                warns.append(item)

        fails.extend(thin_res["fail"])
        fails.extend(unique_res["fail"])

        status = "PASS"
        if fails:
            status = "REJECT"
        elif warns:
            status = "WARN"

        report = {
            "schema_version": "1.0",
            "status": status,
            "summary": {
                "fail_count": len(fails),
                "warn_count": len(warns),
                "checks_run": ["compliance", "similarity", "thin_content", "unique_pack"],
            },
            "checks": {
                "compliance": comp_res.model_dump() if hasattr(comp_res, "model_dump") else comp_res.dict(),
                "similarity": sim_res,
                "thin_content": thin_res,
                "unique_pack": unique_res,
            },
            "fail": fails,
            "warn": warns,
            "meta": {
                "source_type": qa_input.source_type,
                "intent": content_data.get("intent"),
                "language": qa_input.language,
                "disclosure_required": disclosure_required,
            },
        }
        return report

    def to_fixplan(self, report: Dict[str, Any]) -> Dict[str, Any]:
        return self.fixplan.generate(report)
