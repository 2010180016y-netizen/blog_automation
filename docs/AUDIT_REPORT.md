# blog_automation 감사(Audit) 보고서

## 0) 사전 점검 결과
- 실행 지시를 따라 `cd /workspace/blog_automation` 후 `git status --porcelain`가 **빈 상태**임을 확인했습니다.
- `tree -L 4`는 환경에 `tree` 바이너리가 없어 실패했고, 대체로 `rg --files`, `find -maxdepth`로 구조를 파악했습니다.

## 1) 레포 구조/핵심 파일 확인

### Top-level 관찰
- 프론트엔드(Vite/React) + `content_os`(Python FastAPI/검수·발행·트래킹) 혼합 구조.
- 핵심 백엔드 기능(A~F 대응)은 대부분 `content_os/app/*`, `content_os/scripts/*`에 존재.

### 요청한 주요 파일 확인
- `README.md`: AI Studio 샘플 앱 실행 가이드 중심(현재 감사 포인트 A~F와 직접 정합성 낮음).
- `content_os/README.md`: 컴플라이언스 엔진 중심 설명.
- `content_os/pyproject.toml`: FastAPI/uvicorn/sklearn/httpx 등 의존성 명시.
- `.env.example`: Gemini/API URL 수준 변수만 존재.
- 루트 `requirements.txt`는 없음(해당 Python 프로젝트는 `pyproject.toml` 기반).

## 2) A~F 구현 매핑

### A) MY_STORE 상품 동기화(네이버 커머스API: 토큰→목록→상세→DB upsert→refresh_queue)
**판정: 미구현(대부분 공백)**
- 현재 코드에는 네이버 커머스 API 호출, OAuth 토큰 획득/갱신, 상품 목록·상세 페이징, DB `products` upsert, refresh queue 적재가 보이지 않음.
- 유사한 영역은 `refresh`/`store` 모듈이 있으나 전부 mock/로컬 처리 성격:
  - `content_os/app/refresh/detector.py`: 이미 받은 `content_list`, `product_db` 비교 로직만 존재.
  - `content_os/scripts/run_refresh.py`: mock 데이터로만 실행.
  - `content_os/app/store/update_pack.py`: 인사이트 기반 패키지 생성(실제 API 동기화 아님).

### B) AFFILIATE 인입(쇼핑 커넥트: CSV/시트 import → products upsert → 제휴/광고 표기 강제)
**판정: 부분 구현(표기 강제만 부분 충족)**
- CSV/시트 import 파이프라인 및 affiliate product upsert 로직은 부재.
- 대신 sponsored 콘텐츠의 광고/제휴 표기 강제 룰은 있음:
  - `content_os/app/rules/ko_rules.py`, `content_os/app/rules/en_rules.py`
  - `content_os/app/eval/compliance.py`
- 즉, 인입 파이프라인 없음 + 컴플라이언스 룰만 존재.

### C) 네이버 블로그 발행 패키지 생성기(제목/본문/이미지 자리/표기/CTA/FAQ)
**판정: 부분 구현**
- `content_os/app/publish/naver_package.py`가 HTML/meta/zip 패키징 제공.
- 하지만 요구한 구성요소 중 `표기/CTA/FAQ` 강제 템플릿은 없음.
- 이미지는 경로가 존재하면 zip에 복사하는 수준으로 placeholder 정책/검증 없음.

### D) QA 게이트(컴플라이언스, 유사도, thin-content, 유니크팩)
**판정: 부분 구현 (통합 게이트 부재)**
- 구현된 축:
  - 컴플라이언스: `content_os/app/eval/compliance.py`
  - 유사도: `content_os/app/eval/similarity.py`
  - 유니크팩: `content_os/app/pipeline/unique_pack.py`, `content_os/app/seo/validator.py`
  - Naver 품질체크(유사 thin-content 대체 성격 일부): `content_os/app/seo/naver_validator.py`
- 미흡/부재:
  - thin-content 명시 규칙(예: 단어수/문단수 최소 기준) 독립 구현 없음.
  - 위 항목들을 단일 오케스트레이터로 엮어 `PASS/WARN/REJECT` 게이트하는 통합 QA 파이프라인 없음.

### E) 발행 워크플로(상태머신 DRAFT→QA_PASS→READY→PUBLISHED/REJECTED)
**판정: 구현됨(메모리 기반 MVP)**
- `content_os/app/publish/state_machine.py`: 상태/전이 정의.
- `content_os/app/publish/queue.py`: 큐 + human approval 플래그.
- `content_os/app/api/routes_publish.py`: 전이/승인/조회 API 노출.
- 제약: 인메모리 저장으로 프로세스 재시작 시 유실.

### F) 트래킹(ch/cid/sku/intent + 이벤트 수집 + 지표 집계)
**판정: 구현됨(기본형)**
- `content_os/app/track/link_builder.py`: `ch/cid/sku/intent` 파라미터 부착.
- `content_os/app/track/event_collector.py`: SQLite 이벤트 수집.
- `content_os/app/track/metrics.py`: 조회/클릭/전환 집계 + CTR/CVR 계산.
- `content_os/app/api/routes_track.py`: 수집/요약 API 제공.

## 3) 실행 가능성 판정

## 최종 판정: **GO-with-fixes**

### 근거
1. E/F 축(워크플로·트래킹)은 MVP 수준으로 실제 동작 가능한 코드와 테스트가 있음.
2. D의 핵심 요소 일부는 있으나 통합 QA 게이트가 부재하여 운영 일관성이 낮음.
3. A/B의 핵심(외부 소스 인입·동기화·DB upsert)이 사실상 미구현이라, 기획 A~F 전체 기준으로는 즉시 상용 GO 불가.
4. 테스트 스위트에서 실제 실패 3건이 발생하여 기본 품질 신뢰도 저하.

## 4) P0 / P1 / P2 이슈

### P0 (출시 차단)
1. **A 기능 미구현(네이버 커머스 동기화 파이프라인 부재)**
   - 토큰/상품 목록/상세/업서트/refresh_queue 전 과정 없음.
2. **B 인입 파이프라인 미구현(CSV/시트 import + products upsert 부재)**
   - 제휴 링크 소스 ingest가 없어 운영 데이터 유입이 막힘.
3. **테스트 실패 3건(회귀 신호)**
   - `test_ads_linter.test_clean_html`
   - `test_naver_validator.test_valid_naver_content`
   - `test_store_pack.test_insight_extraction`
   - 명령: `python -m unittest discover -s app/tests -p 'test_*.py'` 결과 FAIL.

### P1 (높은 우선순위)
1. **QA 통합 게이트 부재**
   - compliance/similarity/unique_pack/naver_quality 결과를 하나의 승인 정책으로 결합하는 오케스트레이터 없음.
2. **발행 워크플로 영속성 부재**
   - `PublishQueue`가 인메모리 dict여서 재시작 시 상태 손실.
3. **C 패키저 템플릿 강제 부족**
   - CTA/FAQ/광고표기 강제 템플릿 또는 validator 부재.

### P2 (개선)
1. **관측성(Observability) 부족**
   - 동기화·게이트·발행 단계별 구조화 로그/메트릭 표준 미흡.
2. **설정/비밀값 관리 표준화 필요**
   - `.env.example`가 Gemini 중심으로만 작성됨.
3. **저장소 구조 문서화 부족**
   - 루트 README와 `content_os` 기능 간 연계 설명 부족.

## 5) 성능 병목 후보 + 측정 방법(요약)

### 후보 1) 커머스 API 동기화(향후 A 구현 시)
- 병목 포인트: 페이징 N+1 상세 조회, 직렬 처리, 재시도 폭증.
- 측정: SKU당 처리시간 p50/p95, API 호출수/성공률/429 비율, 배치 크기별 Throughput 비교.

### 후보 2) DB upsert
- 병목 포인트: 건별 autocommit, 인덱스 부재, update-path 과다.
- 측정: batch size별 rows/sec, transaction time, DB write lock time, upsert 충돌률.

### 후보 3) 패키지 생성(Unique/Naver)
- 병목 포인트: 이미지 hash/복사, 비디오 keyframe 추출, 압축 I/O.
- 측정: 콘텐츠 1건당 단계별 wall time(해시/추출/압축), 파일 수 대비 선형성, CPU·디스크 사용률.

(자세한 계획은 `docs/PERFORMANCE_PLAN.md`에 분리 정리)

## 6) 디버깅 체크리스트 + 테스트 보강(요약)
- 단계별 체크리스트: 입력 계약 검증 → 상태 전이 검증 → DB 정합성 → 산출물 스키마 검증 → API 계약/성능 확인.
- 테스트 보강:
  - A/B ingestion 계약 테스트(파서/정규화/중복 처리/표기 강제)
  - QA 통합 게이트 E2E
  - 발행/트래킹 idempotency·경쟁상황 테스트
  - 실패 재현 3건에 대한 원인 고정 테스트

(세부 액션/케이스는 `docs/TEST_PLAN.md`에 정리)

## 7) CTO 결론
- 현재 저장소는 **콘텐츠 QA/발행/트래킹 MVP의 조각들**은 갖추었으나, 요청된 A~F 전체 기획 대비 핵심 ingestion/sync 축이 비어 있습니다.
- 따라서 “당장 상용 런칭”은 어렵고, **A/B 구현 + QA 통합 게이트 + 실패 테스트 복구**를 완료하면 실운영 진입이 가능합니다.
