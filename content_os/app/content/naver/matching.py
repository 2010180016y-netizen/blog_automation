from __future__ import annotations

from typing import Dict, List

FUNNEL = ["info", "comparison", "review", "buy"]


def _infer_product_type(product: Dict) -> str:
    source = str(product.get("source_type") or "").upper()
    name = str(product.get("name") or "").lower()
    if source == "AFFILIATE_SHOPPING_CONNECT":
        return "affiliate"
    if any(k in name for k in ["세트", "bundle", "패키지"]):
        return "bundle"
    return "standard"


def choose_template(product: Dict, stage: str) -> str:
    preferred_template = product.get("preferred_template")
    if preferred_template:
        return str(preferred_template)

    ptype = _infer_product_type(product)
    if ptype == "affiliate":
        return f"affiliate_{stage}"
    if ptype == "bundle":
        return f"bundle_{stage}"
    return f"standard_{stage}"


def match_content_plan(product: Dict) -> Dict:
    preferred_intent = product.get("preferred_intent")
    if preferred_intent in FUNNEL:
        stages: List[str] = [str(preferred_intent)]
    else:
        stages = FUNNEL

    template_map = {stage: choose_template(product, stage) for stage in stages}
    return {
        "funnel": stages,
        "template_map": template_map,
        "primary_intent": stages[0],
    }
