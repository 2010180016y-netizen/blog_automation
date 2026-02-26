from __future__ import annotations

from typing import Dict

from .templates import CTA_TEMPLATE, DISCLOSURE_BLOCK, FAQ_TEMPLATE


def generate_naver_affiliate_package(product: Dict) -> Dict:
    title = product.get("title") or product.get("name") or "추천 상품"
    affiliate_url = product.get("affiliate_link") or ""

    html = "\n".join(
        [
            f"<h1>{title}</h1>",
            DISCLOSURE_BLOCK,
            "<p>이 글은 정보 제공 목적이며, 최신 가격/혜택은 아래 링크에서 확인하세요.</p>",
            '<div class="image-slot">[이미지 자리]</div>',
            CTA_TEMPLATE.format(affiliate_url=affiliate_url),
            FAQ_TEMPLATE,
        ]
    )

    return {
        "title": title,
        "html": html,
        "cta": affiliate_url,
        "disclosure_required": True,
        "faq_included": True,
    }
