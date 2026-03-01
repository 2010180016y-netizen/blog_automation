# MY_STORE 상품 동기화 (네이버 커머스 API)

## 개요
`MY_STORE` 상품을 공식 커머스 API로 동기화합니다.

핵심 동작:
- OAuth 토큰 발급 + 캐싱/만료 처리
- 상품 목록 조회(페이지네이션)
- 상품 상세 동시 조회(세마포어 기반 동시성 제한)
- 응답 원문(raw_json) 저장
- 파싱 실패 graceful fail (`parse_status=PARSE_FAIL`)
- 변경 감지 시 `refresh_queue` 적재
- 배치 upsert (`executemany` + 트랜잭션)

## 파일 위치
- 구현: `content_os/app/store/my_store_sync.py`
- 실행 스크립트: `scripts/sync_my_store.py`
- 테스트: `content_os/app/tests/test_my_store_sync.py`

## 환경변수
필수:
- `NAVER_COMMERCE_TOKEN_URL`: OAuth 토큰 엔드포인트
- `NAVER_COMMERCE_API_BASE_URL`: 커머스 API base URL
- `NAVER_COMMERCE_CLIENT_ID`
- `NAVER_COMMERCE_CLIENT_SECRET`

선택:
- `MY_STORE_DB_PATH`: SQLite DB 경로 (기본: `content_os/blogs.db`)

## 실행 방법
```bash
cd /workspace/blog_automation
export NAVER_COMMERCE_TOKEN_URL="https://api.commerce.naver.com/external/v1/oauth2/token"
export NAVER_COMMERCE_API_BASE_URL="https://api.commerce.naver.com/external/v1"
export NAVER_COMMERCE_CLIENT_ID="..."
export NAVER_COMMERCE_CLIENT_SECRET="..."
python scripts/sync_my_store.py
```

## 예시 출력
```json
{
  "fetched": 120,
  "upserted": 120,
  "queued": 34,
  "errors": 0
}
```

## DB 테이블
자동 생성:
- `my_store_products`
  - `sku`(PK), `product_id`, `title`, `price`, `currency`, `status`
  - `payload_hash`, `raw_json`, `parse_status`, `parse_error`, `updated_at`
- `refresh_queue`
  - `sku`, `reason`(`NEW_PRODUCT`/`PRODUCT_CHANGED`), `payload`, `status`, `created_at`

## 실패 처리
- API 호출 실패: retry + exponential backoff
- 상세 조회 실패: 전체 중단 없이 `errors` 카운트 증가 후 계속 진행
- 파싱 실패: 원문 저장 + `PARSE_FAIL`로 저장
