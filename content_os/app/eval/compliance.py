import yaml
from typing import Dict
from ..schemas import ComplianceRequest, ComplianceResult
from ..rules.catalog import RuleCatalog

# Mocking the YAML load for this example
DEFAULT_CONFIG = yaml.safe_load("""
compliance:
  categories: ["뷰티", "리빙", "식품", "건기식"]
  banned_claims:
    ko: ["무조건", "완치", "보장", "부작용 없음", "100%"]
    en: ["guaranteed", "cure", "no side effects", "100%"]
  required_disclosures:
    ko: ["광고", "협찬", "제휴"]
    en: ["sponsored", "affiliate"]
""")

class ComplianceEvaluator:
    def __init__(self, config: Dict = DEFAULT_CONFIG):
        self.catalog = RuleCatalog(config)

    def evaluate(self, request: ComplianceRequest) -> ComplianceResult:
        rules = self.catalog.get_rules(request.language)
        context = {
            "is_sponsored": request.is_sponsored,
            "category": request.category,
            "disclosure_required": request.disclosure_required
        }
        
        fails = []
        warns = []
        suggestions = []
        
        for rule in rules:
            res = rule.evaluate(request.content, context)
            if res:
                if res["status"] == "REJECT":
                    fails.append({"code": res["code"], "detail": res["detail"]})
                else:
                    warns.append({"code": res["code"], "detail": res["detail"]})

        # YMYL Logic
        if request.category in ["건강", "금융"] and "면책" not in request.content:
            warns.append({"code": "YMYL_MISSING_DISCLAIMER", "detail": "YMYL 카테고리이나 면책 문구가 누락되었습니다."})
            suggestions.append("본문 하단에 '본 내용은 전문가의 의견을 대신할 수 없습니다' 등의 면책 문구를 추가하세요.")

        status = "PASS"
        if fails:
            status = "REJECT"
        elif warns:
            status = "WARN"
            
        return ComplianceResult(
            status=status,
            fail=fails,
            warn=warns,
            suggestions=suggestions
        )
