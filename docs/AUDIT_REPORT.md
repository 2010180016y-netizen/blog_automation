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


## 8) 인라인 코멘트 반영: P0 "수익화 최소 기반" 갭 분석

아래 5가지는 “기능이 돌아간다” 수준이 아니라 **매출 극대화 운영**을 위해 필요한 최소 기반이며, 현재 레포 기준으로는 대부분 미구현입니다.

### 8.1 상품 DB(SSOT) 자동 생성/업데이트 + 운영 UI
- 현황: 제품 SSOT 테이블/관리 화면이 없음. 현재 저장은 `contents`, `events` 중심.
- 리스크: 운영자가 "어떤 상품으로 어떤 글을 만들지"와 "제외/우선순위"를 제어할 수 없음.
- P0 액션:
  1) `products`, `product_sources`, `content_product_plan` 스키마 신설
  2) 최소 Admin UI(목록/검색/활성화/우선순위/제외)
  3) 수동 override(강제 제외, 강제 상단 노출) 지원

### 8.2 콘텐츠-상품 매칭 엔진(의도 기반)
- 현황: `track.intent`는 있으나 생성 파이프라인에서 상품 타입·의도 매칭 룰이 없음.
- 리스크: info/compare/review/buy 퍼널 설계 없이 랜덤 템플릿 작성 → 전환율 저하.
- P0 액션:
  1) intent rule set(카테고리/가격대/브랜드/리스크 등) 정의
  2) 템플릿 라우터: info→비교→리뷰→구매 CTA 자동 선택
  3) 매칭 실패 시 fallback 템플릿 및 수동 승인 큐

### 8.3 가격/혜택 변동 대응 장치(제휴 상품)
- 현황: 가격 고정 표기 회피/변동 고지/작성일·업데이트일 자동 삽입 정책이 없음.
- 리스크: 가격 불일치 누적 시 신뢰도 및 전환 붕괴.
- P0 액션:
  1) 제휴 콘텐츠 공통 문구 자동 삽입: "가격/혜택은 변동될 수 있음"
  2) 본문 메타에 `published_at`, `updated_at`, `price_checked_at` 자동 표시
  3) 가격 고정 문구 lint rule(고정 숫자 과다 노출 경고)

### 8.4 CRO 전환형 템플릿 강제
- 현황: 패키지 생성은 가능하나 전환 요소(추천/비추천, 체크리스트, 비교표, FAQ) 강제가 없음.
- 리스크: 하단 버튼 단일 CTA 구조로는 고액 목표 달성 어려움.
- P0 액션:
  1) 템플릿 스키마에 필수 블록 추가
  2) 미충족 시 QA에서 REJECT
  3) 템플릿별 CTR/CVR 계측 태그 자동 부착

### 8.5 A/B 테스트 최소 프레임
- 현황: WordPress AB 플러그인 스캐폴딩은 있으나 실험 설계(가설/샘플/종료조건)와 트래킹 연결이 불완전.
- 리스크: "추측 기반" 카피/배치 변경으로 학습 불가.
- P0 액션:
  1) 실험 단위 정의: CTA 문구/위치/표/리드문
  2) 실험키(`exp_id`, `variant`)를 event schema에 추가
  3) 승자 자동 승급 규칙(최소 샘플·유의확률 기준) 문서화

## 9) 수익화 P0 로드맵 (4주)

### Week 1
- 상품 SSOT 스키마 + ingest 파이프라인 기본 구현
- Admin API(조회/우선순위/제외) 오픈

### Week 2
- intent 매칭 엔진 + 템플릿 라우터 구현
- 가격 변동 고지/타임스탬프 자동 삽입

### Week 3
- CRO 템플릿 강제 + QA reject 연동
- A/B 이벤트 스키마 확장(`exp_id`, `variant`)

### Week 4
- 대시보드(상품별 CTR/CVR, intent별 매출 기여) + 운영 핸드오프
- 승자 템플릿 자동 승급(반자동)


## 10) 인라인 코멘트 반영: P1 "수익 레버 강화" 성장 기능

### 10.1 콘텐츠 클러스터 자동 생성(허브-스포크)
- 현황: 내부링크/클러스터 관련 유틸은 있으나, 수익 퍼널 관점의 허브-스포크 자동 기획/발행 체인이 없음.
- 기대효과: 세션당 페이지 수↑, 체류시간↑, 구매 전환↑.
- P1 액션:
  1) 허브 1개 + 스포크(리뷰/비교/FAQ) N개 자동 생성 플래너
  2) 내부링크 그래프 자동 삽입(허브↔스포크, 스포크↔구매 페이지)
  3) 클러스터 성과 대시보드(세션 깊이, assisted conversion)

### 10.2 콘텐츠 리프레시 자동화(성과 기반 업데이트 큐)
- 현황: refresh 감지는 목업 중심이며, 성과 기반 우선순위 큐/자동 개정 템플릿이 부족.
- 기대효과: "새 글" 외에도 업데이트 기반 SEO 성과 지속.
- P1 액션:
  1) 고성과 글/고매출 SKU 우선 큐(traffic×conversion×freshness score)
  2) 자동 개정 패키지(FAQ 추가, 비교표 갱신, CTA 재최적화)
  3) 업데이트 이력/변경로그와 재색인 트리거

### 10.3 이메일/카카오/푸시 리텐션 장치
- 현황: 재방문 유도 채널(구독/알림) 데이터 모델과 발송 트리거 부재.
- 기대효과: LTV 상승, 재구매/재방문 기반 매출 안정화.
- P1 액션:
  1) 리드 마그넷(가격변동 알림, 재입고 알림, 가이드 PDF) 옵트인 모듈
  2) 채널별 옵트인 동의/수신동의/해지 이력 관리
  3) 이벤트 트리거형 메시지(가격하락, 재입고, 비교표 업데이트)

### 10.4 비교표/추천표 자동 생성기(SSOT 기반)
- 현황: 비교표는 일부 하드코딩 샘플 수준으로, SSOT 동기화 기반 동적 생성이 아님.
- 기대효과: 선택 기준형 콘텐츠 확장으로 상업성 키워드 전환율 개선.
- P1 액션:
  1) SSOT 기반 비교표 렌더러(가격/특징/추천대상/주의점)
  2) intent별 템플릿(info/compare/review/buy) 자동 표 스타일 분기
  3) 표 변경시 자동 diff 배지(업데이트 신뢰 신호)

### 10.5 UGC(리뷰/사진) 수집 + 권리/동의 + 검수
- 현황: UGC ingestion, 권리 증빙, 검수 상태머신 부재.
- 기대효과: 모방 어려운 1차 데이터 축적, 신뢰도 및 SEO 차별화.
- P1 액션:
  1) UGC 제출 파이프라인(텍스트/이미지/동의서)
  2) 권리/초상권/재사용 동의 버전 관리
  3) 검수 상태머신(PENDING→APPROVED/REJECTED) + 공개 이력

## 11) 성장 기능 우선순위 로드맵 (6주)

### Phase 1 (Week 1~2)
- 클러스터 플래너 MVP + 내부링크 자동 삽입
- 성과 기반 refresh score 및 업데이트 큐 구축

### Phase 2 (Week 3~4)
- SSOT 기반 비교표/추천표 자동 생성기
- 업데이트 패키지(FAQ/비교표/CTA) 자동 리렌더

### Phase 3 (Week 5~6)
- 리텐션 옵트인(이메일/카카오/푸시) + 이벤트 트리거
- UGC 수집/권리동의/검수 워크플로 오픈


## 12) 인라인 코멘트 반영: P2 "광고 수익 본격화" 기능

### 12.1 광고 배치 룰 엔진 + RPM 실험 루프
- 현황: 광고 린터 기초 로직은 있으나, 정책 안전/UX 기준과 RPM 실험 프레임이 통합되어 있지 않음.
- 기대효과: 정책 리스크를 낮추면서 광고 단가(RPM) 최적화 반복 가능.
- P2 액션:
  1) 금지 구역 규칙 확장(입력/버튼/CTA 주변, 첫 뷰포트 과밀, 스크롤 방해)
  2) 실험 설계 표준화(광고 슬롯 수/위치/형식 variant)
  3) UX-수익 동시 평가 지표(이탈률, 체류, RPM) 기반 승자 선별

### 12.2 우발 클릭 방지 자동 검사(정책 안전성)
- 현황: 정적 DOM 인접 검사 중심으로 false positive/false negative 가능성이 큼.
- 기대효과: 광고 네트워크 정책 위반 가능성 선제 차단.
- P2 액션:
  1) 렌더 후 시각적 거리 기반 검사(e2e 스냅샷 + 좌표)
  2) 요소 타입별 금지 반경 규칙(CTA/폼/네비게이션)
  3) 배포 전 차단 게이트(위반 시 FAIL)

### 12.3 광고 인프라 자동화(ads.txt 포함)
- 현황: ads.txt/검증/배포 자동 점검 체계가 문서화·자동화되어 있지 않음.
- 기대효과: 승인 이후 수익 안정성 확보, 운영 실수 감소.
- P2 액션:
  1) ads.txt 소스 오브 트루스 + 자동 배포 파이프라인
  2) 배포 후 헬스체크(도메인별 fetch/파서 검증)
  3) 변경 이력/롤백 체계(승인 계정 변경 대응)

## 13) P2 광고 수익화 로드맵 (4주)

### Week 1
- 광고 정책 룰셋 정리 + 금지 구역 검사 강화(정적)

### Week 2
- 시각 기반 우발 클릭 검사(e2e) + 배포 차단 게이트

### Week 3
- RPM 실험 프레임(슬롯/위치/형식 variant) + 이벤트 스키마 확장

### Week 4
- ads.txt 자동 배포/검증/롤백 체계 + 운영 대시보드
