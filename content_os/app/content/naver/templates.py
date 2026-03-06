from __future__ import annotations

DISCLOSURE_BLOCK = """
<div class="disclosure">
  <strong>[광고/제휴 안내]</strong>
  본 콘텐츠에는 제휴 링크가 포함될 수 있으며, 구매 시 일정 수수료를 받을 수 있습니다.
  가격/혜택은 작성일 기준이며 변동될 수 있습니다.
</div>
""".strip()

DATE_BLOCK_TEMPLATE = """
<div class="date-block">
  <p>작성일: {written_date}</p>
  <p>업데이트일: {updated_date}</p>
  <p>※ 가격/혜택은 실시간 변동 가능하므로 반드시 링크에서 최신값을 확인하세요.</p>
</div>
""".strip()

CTA_TEMPLATE_A = """
<div class="cta-block cta-bottom">
  <a href="{affiliate_url}" target="_blank" rel="nofollow sponsored">최신 가격/혜택 확인하기</a>
</div>
""".strip()

CTA_TEMPLATE_B = """
<div class="cta-block cta-inline">
  <a href="{affiliate_url}" target="_blank" rel="nofollow sponsored">지금 조건 비교하고 구매하기</a>
</div>
""".strip()

RECOMMENDATION_TEMPLATE = """
<h3>추천 대상 / 비추천 대상</h3>
<ul>
  <li>추천: 문제를 빠르게 해결해야 하고, 사용 빈도가 높은 사용자</li>
  <li>비추천: 단기 1회 사용만 필요하거나 예산이 매우 제한적인 사용자</li>
</ul>
""".strip()

CHECKLIST_TEMPLATE = """
<h3>선택 체크리스트</h3>
<ul>
  <li>사용 목적이 명확한가?</li>
  <li>월 예산 대비 유지비를 감당 가능한가?</li>
  <li>AS/교환 정책을 확인했는가?</li>
</ul>
""".strip()

COMPARISON_TABLE_TEMPLATE = """
<h3>대체 상품 비교표</h3>
<table>
  <thead><tr><th>옵션</th><th>핵심 장점</th><th>주의점</th></tr></thead>
  <tbody>
    <tr><td>현재 상품</td><td>균형형</td><td>가격 변동 가능</td></tr>
    <tr><td>대체안 A</td><td>가성비</td><td>부가 기능 제한</td></tr>
    <tr><td>대체안 B</td><td>프리미엄</td><td>초기 비용 높음</td></tr>
  </tbody>
</table>
""".strip()

FAQ_TEMPLATE = """
<h3>FAQ</h3>
<ul>
  <li>Q. 가격은 고정인가요? A. 아니요. 가격/혜택은 수시로 변경될 수 있습니다.</li>
  <li>Q. 최신 정보는 어디서 확인하나요? A. 본문의 공식 제휴 링크에서 확인하세요.</li>
</ul>
""".strip()
