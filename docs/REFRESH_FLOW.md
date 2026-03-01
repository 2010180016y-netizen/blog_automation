# REFRESH FLOW

## 목적
MY_STORE 상품 정보 및 FAQ/CS 변경을 감지해, 이미 발행된 콘텐츠(`content_queue.status = PUBLISHED`)에 대한 수정 지시서(`update_pack`)를 자동 생성합니다.

## 트리거
다음 이벤트가 발생하면 콘텐츠 리프레시를 시작합니다.

1. **MY_STORE 상품 변경**
   - 가격(`price`)
   - 옵션(`options`)
   - 배송 정보(`shipping`)
   - 판매 상태(`status`)
2. **FAQ/CS 변경**
   - FAQ 신규 항목 추가(`faq_added`)
   - CS 응대 정책/문구 변경(`cs`)

## 처리 단계
1. 변경 이벤트 수신 (`product_id`, `sku`, `before`, `after`).
2. 변경 필드 비교로 트리거 목록 계산.
3. `content_queue`에서 `PUBLISHED` 상태 콘텐츠 중 같은 `product_id` 또는 `sku`를 가진 항목 조회.
4. 영향 콘텐츠별 `update_pack` 생성:
   - 수정할 섹션/문단 위치
   - 새 데이터(`new_data`) / 기존 데이터(`old_data`)
   - 변경 로그(`change_log`)
5. `out/update_packs/{content_id}.json` 경로로 저장.

## update_pack 위치 매핑 규칙
- `price` → `가격/혜택` 섹션, 2문단
- `options` → `옵션 안내` 섹션, 3문단
- `shipping` → `배송/교환` 섹션, 1문단
- `status` → `구매 가능 상태` 섹션, 1문단
- `faq_added` → `FAQ` 섹션, 1문단
- `cs` → `FAQ` 섹션, 2문단

## 운영 예시
```python
from app.refresh.content_refresh import ContentRefreshService, RefreshEvent

service = ContentRefreshService(db_path="blogs.db", out_dir="out/update_packs")
event = RefreshEvent(
    product_id="PID-1001",
    sku="SKU-1001",
    before={"price": 19900, "faq": ["배송은?"], "cs": "24시간 내 응대"},
    after={"price": 17900, "faq": ["배송은?", "당일발송 가능?"], "cs": "12시간 내 응대"},
)
paths = service.process_event(event)
print(paths)
```

## 산출물
- `out/update_packs/{content_id}.json`
- 변경 로그 기반 재작성 입력 데이터(후속 LLM 편집 파이프라인 연계 가능)
