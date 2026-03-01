import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

SourceType = Literal["MY_STORE", "AFFILIATE"]
IntentType = Literal["info", "review", "compare", "story"]
VariantType = Literal["A", "B"]

REQUIRED_SECTIONS = [
    "사용법",
    "공식(근거)",
    "예시",
    "추천 대상 / 비추천 대상",
    "구매 전 체크리스트",
    "경쟁/대체 옵션 비교표",
    "FAQ",
    "주의사항",
    "엣지케이스",
]


@dataclass
class PackageInput:
    content_id: str
    product_id: str
    source_type: SourceType
    intent: IntentType


class NaverPackageGenerator:
    def __init__(self, output_root: str = "out/naver_packages"):
        self.output_root = output_root

    def _intent_title(self, intent: IntentType) -> str:
        mapping = {
            "info": "문제 해결 가이드",
            "review": "실사용 리뷰",
            "compare": "비교 분석",
            "story": "사용자 스토리",
        }
        return mapping[intent]

    def _append_variant_param(self, url: str, variant: Optional[VariantType]) -> str:
        if variant is None:
            return url
        u = urlparse(url)
        query = parse_qs(u.query)
        query["variant"] = [variant]
        return urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(query, doseq=True), u.fragment))

    def _disclosure_block(self, source_type: SourceType) -> str:
        if source_type != "AFFILIATE":
            return ""
        return (
            "<p><strong>[제휴 안내]</strong> 본 글에는 제휴 링크가 포함될 수 있으며, "
            "링크를 통한 구매 시 일정 수수료를 제공받을 수 있습니다.</p>\n"
            "<p><em>가격/혜택은 시점에 따라 변동될 수 있습니다. 최신 정보는 링크에서 확인하세요.</em></p>"
        )

    def _build_sections(self, intent: IntentType, product_id: str) -> List[Dict[str, str]]:
        base = {
            "사용법": f"{product_id} 사용 전 체크리스트와 3단계 적용 순서를 정리합니다.",
            "공식(근거)": "제조사 스펙, 공인 문서, 공개된 수치 기반으로 판단 기준을 제시합니다.",
            "예시": "실제 사용 상황 2~3개를 가정해 선택 기준을 적용합니다.",
            "FAQ": "구매 전 가장 많이 묻는 질문 최소 6개를 답변 형태로 제공합니다.",
            "주의사항": "오용/과장/환경 차이로 인한 결과 편차를 명시합니다.",
            "엣지케이스": "일반 조건과 다른 환경(예: 예산 제약, 공간 제약)에서의 대안을 정리합니다.",
        }

        if intent == "review":
            base["예시"] = "1주/2주 사용 시점별 체감 포인트와 한계를 함께 기록합니다."
        elif intent == "compare":
            base["공식(근거)"] = "동급 대체 상품 2~3개와 핵심 스펙/가격/장단점을 비교합니다."
        elif intent == "story":
            base["사용법"] = "사용자의 문제-시도-개선 흐름으로 단계별 적용법을 설명합니다."

        return [{"title": k, "content": v} for k, v in base.items()]

    def _cta_block(self, cta_link: str, variant: Optional[VariantType]) -> str:
        variant_text = {
            "A": "지금 혜택 확인하기",
            "B": "최신 가격/리뷰 보고 결정하기",
            None: "자세히 보기",
        }
        lead = {
            "A": "핵심 장점을 확인했다면 바로 가격/혜택을 확인해보세요.",
            "B": "체크리스트를 마쳤다면 최신 스펙/후기를 보고 최종 결정하세요.",
            None: "핵심 요약을 확인했다면 상세 정보에서 최신 스펙/혜택을 확인하세요.",
        }
        label = variant_text.get(variant, variant_text[None])
        description = lead.get(variant, lead[None])
        return (
            "<div class='cta'>"
            f"<p>{description}</p>"
            f"<a href='{cta_link}' data-variant='{variant or ''}' target='_blank' rel='nofollow noopener'>{label}</a>"
            "</div>"
        )

    def _render_html(
        self,
        payload: PackageInput,
        title: str,
        summary: str,
        tags: List[str],
        cta_link: str,
        variant: Optional[VariantType] = None,
    ) -> str:
        sections = self._build_sections(payload.intent, payload.product_id)
        disclosure_html = self._disclosure_block(payload.source_type)

        section_html = "\n".join([f"<h2>{s['title']}</h2>\n<p>{s['content']}</p>" for s in sections])

        target_html = (
            "<h2>추천 대상 / 비추천 대상</h2>"
            "<ul>"
            "<li><strong>추천 대상</strong>: 빠른 설치와 무난한 성능을 원하는 사용자</li>"
            "<li><strong>추천 대상</strong>: 유지비 예측이 중요한 사용자</li>"
            "<li><strong>비추천 대상</strong>: 최고 성능만 우선하는 하이엔드 사용자</li>"
            "<li><strong>비추천 대상</strong>: 즉시 커스텀 확장이 필수인 사용자</li>"
            "</ul>"
        )

        checklist_html = (
            "<h2>구매 전 체크리스트</h2>"
            "<ol>"
            "<li>총 예산(본체/부속/유지비)을 함께 계산했는가?</li>"
            "<li>설치 공간/호환 규격이 실제 환경과 맞는가?</li>"
            "<li>필수 옵션과 불필요 옵션을 구분했는가?</li>"
            "<li>배송 리드타임과 설치 가능 일정을 확인했는가?</li>"
            "<li>반품/교환/보증 정책의 비용 조건을 확인했는가?</li>"
            "<li>최신 가격/쿠폰/재고 변동을 최종 확인했는가?</li>"
            "</ol>"
        )

        comparison_html = (
            "<h2>경쟁/대체 옵션 비교표</h2>"
            "<table border='1'>"
            "<thead><tr><th>옵션</th><th>강점</th><th>약점</th><th>추천 상황</th></tr></thead>"
            "<tbody>"
            f"<tr><td>{payload.product_id}</td><td>균형형 스펙</td><td>최고성능은 아님</td><td>일반 사용자</td></tr>"
            "<tr><td>대체 옵션 A</td><td>저렴한 가격</td><td>내구성 보통</td><td>예산 최우선</td></tr>"
            "<tr><td>대체 옵션 B</td><td>높은 성능</td><td>가격 부담</td><td>성능 최우선</td></tr>"
            "</tbody></table>"
        )

        faq_html = (
            "<ul>"
            "<li>Q. 초보자도 바로 사용할 수 있나요? A. 사용법 섹션의 체크리스트를 먼저 확인하세요.</li>"
            "<li>Q. 대체 상품과 차이는? A. 비교 관점은 공식(근거)·주의사항 섹션에 요약했습니다.</li>"
            "<li>Q. 가격은 언제 확인하는 게 정확한가요? A. 결제 직전 상품 상세 페이지를 다시 확인하세요.</li>"
            "<li>Q. 배송 지연 시 대응은? A. 배송/교환 정책과 판매자 공지를 우선 확인하세요.</li>"
            "<li>Q. 옵션 선택이 어렵습니다. A. 구매 전 체크리스트 3번 항목 기준으로 필수 옵션만 고르세요.</li>"
            "<li>Q. A/S 기간은 어디서 확인하나요? A. 제품 상세의 보증 조건과 공식 정책 페이지를 확인하세요.</li>"
            "</ul>"
        )

        cta_html = self._cta_block(cta_link, variant=variant)
        cta_top = cta_html if variant == "A" else ""
        cta_bottom = cta_html if variant != "A" else ""

        return (
            f"<article data-intent='{payload.intent}' data-source-type='{payload.source_type}' data-variant='{variant or ''}'>"
            f"<h1>{title}</h1>"
            f"<p>{summary}</p>"
            f"{disclosure_html}"
            f"{cta_top}"
            f"{section_html}"
            f"{target_html}"
            f"{checklist_html}"
            f"{comparison_html}"
            "<h2>FAQ</h2>"
            f"{faq_html}"
            f"{cta_bottom}"
            "</article>"
        )

    def _meta(self, payload: PackageInput, cta_link: str, variant: Optional[VariantType] = None) -> Dict:
        title = f"[{payload.intent.upper()}] {payload.product_id} {self._intent_title(payload.intent)}"
        if variant:
            title = f"{title} (Variant {variant})"
        summary = (
            f"{payload.product_id}를 {payload.intent} 관점으로 분석한 네이버 블로그 발행 패키지입니다. "
            "사용법/근거/예시/추천·비추천/체크리스트/비교표/FAQ/주의사항/엣지케이스를 포함합니다."
        )
        tags = [payload.product_id, payload.intent, payload.source_type, "네이버블로그", "구매가이드"]
        return {
            "title": title,
            "summary": summary,
            "tags": tags,
            "category": "커머스/가이드",
            "cta_link": cta_link,
            "content_id": payload.content_id,
            "product_id": payload.product_id,
            "source_type": payload.source_type,
            "intent": payload.intent,
            "variant": variant,
        }


    @staticmethod
    def _write_text_if_changed(path: str, body: str) -> bool:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                if f.read() == body:
                    return False
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return True

    @staticmethod
    def _write_json_if_changed(path: str, payload: Dict) -> bool:
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        return NaverPackageGenerator._write_text_if_changed(path, rendered)

    def _validate_required_sections(self, html: str, source_type: SourceType) -> Dict:
        missing = [sec for sec in REQUIRED_SECTIONS if f"<h2>{sec}</h2>" not in html]
        faq_count = html.count("<li>Q.")
        if faq_count < 6:
            missing.append("FAQ(최소 6개)")
        if source_type == "AFFILIATE" and "[제휴 안내]" not in html:
            missing.append("제휴 표기")
        if source_type == "AFFILIATE" and "가격/혜택은 시점에 따라 변동될 수 있습니다" not in html:
            missing.append("가격/혜택 변동 문구")

        return {"status": "REJECT" if missing else "PASS", "missing_sections": missing}

    def create_package(
        self,
        content_id: str,
        product_id: str,
        source_type: SourceType,
        intent: IntentType,
        cta_link: str,
        variant: Optional[VariantType] = None,
    ) -> Dict:
        if source_type not in {"MY_STORE", "AFFILIATE"}:
            raise ValueError("source_type must be MY_STORE or AFFILIATE")
        if intent not in {"info", "review", "compare", "story"}:
            raise ValueError("intent must be one of info/review/compare/story")
        if variant not in {None, "A", "B"}:
            raise ValueError("variant must be A/B or None")

        payload = PackageInput(content_id=content_id, product_id=product_id, source_type=source_type, intent=intent)

        package_suffix = f"_{variant}" if variant else ""
        package_dir = os.path.join(self.output_root, f"{content_id}{package_suffix}")
        images_dir = os.path.join(package_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        for i in range(1, 4):
            ph = os.path.join(images_dir, f"placeholder_{i}.txt")
            if not os.path.exists(ph):
                with open(ph, "w", encoding="utf-8") as f:
                    f.write(f"unique image placeholder {i} for {content_id}{package_suffix}\n")

        t_render = time.perf_counter()
        tracked_link = self._append_variant_param(cta_link, variant=variant)
        meta = self._meta(payload, cta_link=tracked_link, variant=variant)
        html = self._render_html(payload, meta["title"], meta["summary"], meta["tags"], tracked_link, variant=variant)
        render_sec = time.perf_counter() - t_render
        qa = self._validate_required_sections(html, source_type=source_type)

        if qa["status"] == "REJECT":
            return {
                "status": "REJECT",
                "reason": "MISSING_REQUIRED_SECTIONS",
                "missing_sections": qa["missing_sections"],
                "package_dir": package_dir,
                "variant": variant,
                "render_sec": round(render_sec, 6),
            }

        post_html = os.path.join(package_dir, "post.html")
        meta_json = os.path.join(package_dir, "meta.json")

        t_write = time.perf_counter()
        wrote_post = self._write_text_if_changed(post_html, html)
        wrote_meta = self._write_json_if_changed(meta_json, meta)
        write_sec = time.perf_counter() - t_write

        return {
            "status": "PASS",
            "package_dir": package_dir,
            "post_html": post_html,
            "meta_json": meta_json,
            "images_dir": images_dir,
            "variant": variant,
            "qa": qa,
            "render_sec": round(render_sec, 6),
            "io": {
                "wrote_post_html": wrote_post,
                "wrote_meta_json": wrote_meta,
                "write_sec": round(write_sec, 6),
            },
        }

    def create_ab_variants(
        self,
        content_id: str,
        product_id: str,
        source_type: SourceType,
        intent: IntentType,
        cta_link: str,
    ) -> Dict[str, Dict]:
        a = self.create_package(content_id, product_id, source_type, intent, cta_link, variant="A")
        b = self.create_package(content_id, product_id, source_type, intent, cta_link, variant="B")
        return {"content_id": content_id, "variants": {"A": a, "B": b}}
