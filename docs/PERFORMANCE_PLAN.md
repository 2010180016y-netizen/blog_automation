# PERFORMANCE_PLAN

## 목표
A(커머스 동기화), DB upsert, C(패키지 생성) 구간의 병목을 수치화하고, 릴리즈 전 성능 예산(SLO)을 고정한다.

---

## 1) 측정 원칙
- 모든 단계에 `trace_id`, `content_id`, `sku`를 공통 태그로 남긴다.
- 평균(mean) 대신 p50/p95/p99를 우선 지표로 본다.
- 단건 최적화보다 배치(실운영) 처리량 기준으로 판단한다.

---

## 2) 병목 후보별 계획

## A. MY_STORE 동기화 (토큰→목록→상세→upsert→refresh enqueue)

### 가설
1. 상세조회 N+1이 전체 시간을 지배한다.
2. API rate limit(429) 재시도로 tail latency가 커진다.
3. 변경 없는 SKU까지 풀스캔하면 불필요 호출이 급증한다.

### 계측 항목
- `sync_total_seconds`
- `token_fetch_seconds`
- `list_fetch_seconds`
- `detail_fetch_seconds`(SKU별)
- `api_requests_total{endpoint,status}`
- `api_429_total`, `retry_total`
- `changed_sku_ratio`
- `refresh_queue_enqueue_total`

### 실험 시나리오
- 배치 크기: 50 / 200 / 500 SKU
- 동시성: 1 / 5 / 10 worker
- 캐시/증분동기화 on/off
- 결과 비교: 처리량(rows/s), p95, 429 비율

### 목표 예시(SLO)
- 1,000 SKU 기준 전체 동기화 10분 이내
- detail fetch p95 < 500ms
- 429 비율 < 1%

---

## B. DB upsert (products + refresh_queue)

### 가설
1. row-by-row autocommit은 SQLite/관계형 DB에서 lock 경쟁을 유발한다.
2. upsert key 인덱스 부재 시 성능이 급격히 저하된다.
3. 불필요 update(동일 데이터 재쓰기)가 write 증폭을 만든다.

### 계측 항목
- `db_upsert_rows_total`
- `db_upsert_seconds`
- `db_txn_seconds`
- `db_lock_wait_seconds`
- `db_conflict_total`
- `no_change_skip_total`

### 실험 시나리오
- 커밋 전략: row 단위 vs batch(100/500/1000)
- 인덱스 유무 비교(예: sku unique)
- 변경감지(hash) 기반 skip on/off

### 목표 예시
- 10k upsert < 120초
- batch mode가 row mode 대비 3배 이상 향상

---

## C. 패키지 생성 (Naver package + Unique pack)

### 가설
1. 이미지 해시/복사와 zip I/O가 CPU/디스크를 지배한다.
2. 비디오 keyframe 추출이 긴 tail latency를 만든다.

### 계측 항목
- `package_build_seconds`
- `image_hash_seconds`
- `image_copy_seconds`
- `keyframe_extract_seconds`
- `zip_seconds`
- `package_size_bytes`

### 실험 시나리오
- 이미지 수: 3 / 10 / 30
- 비디오 유무
- 압축 레벨(낮음/기본/높음)

### 목표 예시
- 일반 포스트(이미지 10장) 패키지 생성 p95 < 3초
- 비디오 포함 포스트 p95 < 10초

---

## 3) 프로파일링/벤치 도구 제안
- Python: `time.perf_counter`, `cProfile`, `py-spy`(샘플링)
- DB: `EXPLAIN QUERY PLAN` + 트랜잭션 시간 로깅
- 시스템: `pidstat`, `iostat`(CPU/I/O 병목 판별)
- 리포트: 배치 테스트 결과를 CSV로 저장 후 주간 비교

---

## 4) 즉시 실행 액션(1주)
1. 동기화/업서트/패키지 단계별 타이머 계측 코드 추가.
2. 배치 사이즈 실험 스크립트 작성(50/200/500).
3. p95 기준으로 초기 성능 예산표 작성.
4. 성능 회귀 검출용 CI 간이 벤치(작은 데이터셋) 추가.

---

## 5) 종료 기준(Definition of Done)
- 각 파이프라인에 대해 p50/p95가 측정되고, 기준선을 문서화한다.
- 릴리즈 직전 동일 시나리오 재측정 시 기준 대비 열화 < 15%.
- 병목 구간별 개선 PR과 전/후 지표가 남아 있다.
