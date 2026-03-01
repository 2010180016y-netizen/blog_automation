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


---

## 6) 수익화 P0 기능 성능 플랜 (추가)

## 6.1 상품 SSOT Admin/API
- 지표
  - `admin_product_list_p95_ms`
  - `admin_priority_update_p95_ms`
  - `product_search_qps`
- 측정 커맨드(예시)
  - `python scripts/bench_admin_api.py --endpoint /admin/products --concurrency 20 --duration 60`
- 로깅 포인트
  - 조회 필터(카테고리/상태), 페이지네이션, 정렬 키 사용량

## 6.2 콘텐츠-상품 매칭 엔진
- 지표
  - `match_engine_latency_p95_ms`
  - `fallback_ratio`
  - `intent_distribution_drift`
- 측정 커맨드(예시)
  - `python scripts/bench_match_engine.py --items 10000 --ruleset default`
- 로깅 포인트
  - 입력 피처, 매칭 룰 ID, 선택 템플릿 ID, fallback 여부

## 6.3 가격/혜택 변동 고지 자동삽입
- 지표
  - `disclaimer_injection_ms`
  - `price_staleness_hours`
  - `price_fixed_literal_detected_total`
- 측정 커맨드(예시)
  - `python scripts/bench_disclosure.py --posts 5000`
- 로깅 포인트
  - 본문 생성 시점의 가격 확인 타임스탬프, 마지막 갱신 시간

## 6.4 CRO 템플릿 + A/B 최소 프레임
- 지표
  - `template_render_p95_ms`
  - `ab_assignment_p95_ms`
  - `experiment_event_loss_ratio`
- 측정 커맨드(예시)
  - `python scripts/bench_template_render.py --templates cro_buy,cro_compare --n 2000`
  - `python scripts/bench_ab_assignment.py --users 100000 --variants 2`
- 로깅 포인트
  - `exp_id`, `variant`, CTA 위치, 표 구성 버전, 리드문 버전

## 6.5 수익 KPI 연동 SLO (성능 + 사업)
- 주간 최소 목표
  - 실험 대상 트래픽 비중 30% 이상
  - 실험 이벤트 유실률 0.5% 이하
  - 가격 stale(24h 초과) 콘텐츠 비율 5% 이하
- 릴리즈 차단 기준
  - A/B 이벤트 손실률 > 2%
  - match fallback 비율 > 20%
  - admin 조회 p95 > 800ms


---

## 7) P1 성장 기능 성능 플랜 (추가)

## 7.1 클러스터 자동 생성/내부링크
- 지표
  - `cluster_plan_latency_p95_ms`
  - `internal_link_insert_latency_ms`
  - `avg_pages_per_session`
- 측정 커맨드(예시)
  - `python scripts/bench_cluster_builder.py --hubs 100 --spokes-per-hub 6`
- 로깅 포인트
  - 허브/스포크 개수, 링크 삽입 수, 링크 실패/충돌 건수

## 7.2 성과기반 리프레시 큐
- 지표
  - `refresh_score_compute_ms`
  - `refresh_queue_depth`
  - `time_to_refresh_publish_hours`
- 측정 커맨드(예시)
  - `python scripts/bench_refresh_queue.py --posts 50000 --topk 5000`
- 로깅 포인트
  - 점수 구성요소(traffic, conversion, freshness), 큐 진입/처리 시각

## 7.3 리텐션 채널(이메일/카카오/푸시)
- 지표
  - `subscription_optin_latency_ms`
  - `message_trigger_delay_ms`
  - `retention_conversion_rate`
- 측정 커맨드(예시)
  - `python scripts/bench_retention_trigger.py --events 100000`
- 로깅 포인트
  - 채널, 트리거 이벤트, 발송 성공/실패 코드, 재시도 횟수

## 7.4 비교표/추천표 자동 생성
- 지표
  - `comparison_table_render_p95_ms`
  - `table_staleness_hours`
  - `table_update_propagation_ms`
- 측정 커맨드(예시)
  - `python scripts/bench_comparison_table.py --skus 20000 --variants 4`
- 로깅 포인트
  - 표 버전, 데이터 소스 버전(SSOT snapshot), diff 건수

## 7.5 UGC 수집/검수 파이프라인
- 지표
  - `ugc_ingest_latency_ms`
  - `ugc_review_turnaround_hours`
  - `ugc_rights_validation_fail_ratio`
- 측정 커맨드(예시)
  - `python scripts/bench_ugc_pipeline.py --submissions 50000`
- 로깅 포인트
  - 동의서 버전, 저작권/초상권 체크 결과, 검수 상태 전이


---

## 8) P2 광고 수익화 성능/실험 플랜 (추가)

## 8.1 광고 배치 룰 엔진 성능
- 지표
  - `ad_lint_latency_p95_ms`
  - `policy_violation_detect_rate`
  - `false_positive_rate`
- 측정 커맨드(예시)
  - `python scripts/bench_ad_linter.py --pages 20000 --ruleset strict`
- 로깅 포인트
  - 위반 규칙 ID, 요소 타입, 문서 위치, 빌드 차단 여부

## 8.2 우발 클릭 방지(e2e 시각 검사)
- 지표
  - `visual_guard_latency_ms`
  - `unsafe_ad_proximity_count`
  - `pre_release_block_ratio`
- 측정 커맨드(예시)
  - `python scripts/bench_ad_visual_guard.py --urls-file urls.txt --viewport mobile,desktop`
- 로깅 포인트
  - 광고 슬롯 bbox, CTA/입력 bbox, 최소 거리(px), 스크린샷 경로

## 8.3 RPM 실험 루프
- 지표
  - `rpm_by_variant`
  - `bounce_rate_delta`
  - `session_duration_delta`
- 측정 커맨드(예시)
  - `python scripts/bench_rpm_experiment.py --exp ad_slot_layout --variants 3 --days 14`
- 로깅 포인트
  - `exp_id`, `variant`, 슬롯수/위치/형식, 트래픽 분배율

## 8.4 ads.txt 자동화 신뢰성
- 지표
  - `ads_txt_deploy_latency_ms`
  - `ads_txt_validation_pass_rate`
  - `ads_txt_drift_detected_total`
- 측정 커맨드(예시)
  - `python scripts/check_ads_txt.py --domains domains.txt --expect config/ads_txt_sources.yaml`
- 로깅 포인트
  - 도메인별 fetch 결과, 파싱 결과, 불일치 라인, 롤백 여부

## 8.5 광고 수익화 릴리즈 차단 기준
- `policy_violation_detect_rate`가 임계치 초과 시 릴리즈 차단
- 우발 클릭 위험 슬롯 검출 시 자동 FAIL
- ads.txt 검증 실패 도메인 존재 시 배포 차단
