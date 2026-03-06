from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict

from .matching import match_content_plan
from .templates import (
    CHECKLIST_TEMPLATE,
    COMPARISON_TABLE_TEMPLATE,
    CTA_TEMPLATE_A,
    CTA_TEMPLATE_B,
    DATE_BLOCK_TEMPLATE,
    DISCLOSURE_BLOCK,
    FAQ_TEMPLATE,
    RECOMMENDATION_TEMPLATE,
)


def _pick_ab_variant(seed: str) -> str:
    h = hashlib.md5(seed.encode("utf-8")).hexdigest()
    return "B" if int(h[-1], 16) % 2 else "A"


def generate_naver_affiliate_package(product: Dict) -> Dict:
    title = product.get("title") or product.get("name") or "추천 상품"
    affiliate_url = product.get("affiliate_link") or ""
    sku = str(product.get("partner_product_id") or product.get("sku") or title)
    ab_variant = str(product.get("ab_variant") or _pick_ab_variant(sku))

    now = datetime.now().strftime("%Y-%m-%d")
    written_date = str(product.get("written_date") or now)
    updated_date = str(product.get("updated_date") or now)

    cta_top = CTA_TEMPLATE_B.format(affiliate_url=affiliate_url)
    cta_bottom = CTA_TEMPLATE_A.format(affiliate_url=affiliate_url)

    plan = match_content_plan(product)
    primary_intent = plan["primary_intent"]

    blocks = [
        f"<h1>{title}</h1>",
        DATE_BLOCK_TEMPLATE.format(written_date=written_date, updated_date=updated_date),
        DISCLOSURE_BLOCK,
        "<p>이 글은 정보 제공 목적이며, 최신 가격/혜택은 아래 링크에서 확인하세요.</p>",
        '<div class="image-slot">[이미지 자리]</div>',
        RECOMMENDATION_TEMPLATE,
        CHECKLIST_TEMPLATE,
        COMPARISON_TABLE_TEMPLATE,
        FAQ_TEMPLATE,
    ]

    if ab_variant == "B":
        blocks.insert(4, cta_top)
        blocks.append(cta_bottom)
    else:
        blocks.append(cta_bottom)

    html = "\n".join(blocks)

    return {
        "title": title,
        "html": html,
        "cta": affiliate_url,
        "disclosure_required": True,
        "faq_included": True,
        "ab_variant": ab_variant,
        "written_date": written_date,
        "updated_date": updated_date,
        "intent": primary_intent,
        "template": plan["template_map"].get(primary_intent),
    }
