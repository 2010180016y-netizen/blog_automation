import os
from pathlib import Path
from typing import Dict, Tuple

import yaml

from ..schemas import ComplianceRequest, ComplianceResult
from ..rules.catalog import RuleCatalog


DEFAULT_RULESET_PATH = Path(__file__).resolve().parent.parent / "rules" / "compliance_rules.v1.yaml"


def load_ruleset(path: str = None) -> Tuple[Dict, str]:
    ruleset_path = Path(path or os.getenv("COMPLIANCE_RULESET_PATH", str(DEFAULT_RULESET_PATH)))
    with open(ruleset_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    version = str(config.get("version", "unversioned"))
    return config, version


class ComplianceEvaluator:
    def __init__(self, config: Dict = None, ruleset_path: str = None):
        if config is None:
            loaded_config, version = load_ruleset(ruleset_path)
            self.ruleset_version = version
            self.config = loaded_config
        else:
            self.ruleset_version = str(config.get("version", "inline"))
            self.config = config

        self.catalog = RuleCatalog(self.config)

    def evaluate(self, request: ComplianceRequest) -> ComplianceResult:
        rules = self.catalog.get_rules(request.language)
        context = {
            "is_sponsored": request.is_sponsored,
            "category": request.category,
        }

        fails = []
        warns = []
        suggestions = [f"RULESET_VERSION={self.ruleset_version}"]

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
            suggestions=suggestions,
        )
