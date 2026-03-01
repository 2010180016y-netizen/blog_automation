# TEST_PLAN

## 1) 현재 테스트 상태 요약
- 실행 명령: `cd content_os && python -m unittest discover -s app/tests -p 'test_*.py'`
- 결과: 총 38개 중 3개 실패.
  1. `test_ads_linter.TestAdsLinter.test_clean_html`
  2. `test_naver_validator.TestNaverValidator.test_valid_naver_content`
  3. `test_store_pack.TestStorePack.test_insight_extraction`

---

## 2) 디버깅 체크리스트 (운영 장애/테스트 실패 공통)

### A. 입력 계약(Contract) 확인
- API/스크립트 입력 스키마가 기대 필드·타입을 만족하는가?
- 문자열 정규화(공백/대소문자/한글 조사) 차이로 룰 오탐이 나는가?
- 기본값 주입 로직이 의도와 일치하는가?

### B. 비즈니스 룰 확인
- sponsored=true일 때 표기 강제 룰이 콘텐츠 상단 범위를 올바르게 검사하는가?
- Naver 품질 룰(링크 밀도, 반복어 탐지)이 실제 정상 케이스를 과도하게 reject하지 않는가?
- 인사이트 추출 소스 필터가 요구사항과 테스트 기대값이 일치하는가?

### C. 상태 전이/워크플로 확인
- DRAFT→QA_PASS→READY→PUBLISHED 전이가 모두 검증되는가?
- human approval required 플래그가 READY/PUBLISHED 단계에서 정확히 작동하는가?

### D. 저장소(DB) 확인
- 이벤트 저장 시 누락 컬럼/JSON 직렬화 오류가 없는가?
- 집계 쿼리의 분모 0 처리, 이벤트 타입 분류가 정책과 일치하는가?

### E. 산출물 검증
- Naver 패키지(zip)에 필수 파일(content/meta/이미지)이 실제 포함되는가?
- unique pack의 최소 이미지 규칙/alt_text 생성이 파일 시스템 상태에 따라 안정적인가?

---

## 3) 실패 3건에 대한 우선 보수 계획

## P0-1) `test_clean_html` 실패
- 점검 파일: `app/ads/linter.py`, `app/tests/test_ads_linter.py`
- 의심 원인:
  - 클린 HTML에서도 CTA 주변 금칙 요소 탐지 조건이 과민.
  - DOM sibling 탐색 범위 또는 class 검사 로직이 false positive를 유발.
- 조치:
  1. 테스트 fixture HTML을 기준으로 중간 파싱 결과를 출력해 어떤 노드가 위반으로 잡히는지 확인.
  2. 탐지 범위를 명확히(직계/인접 노드만) 제한.
  3. 정상/경계/실패 케이스 3종 추가.

## P0-2) `test_valid_naver_content` 실패
- 점검 파일: `app/seo/naver_validator.py`, `app/tests/test_naver_validator.py`
- 의심 원인:
  - 현재 링크 밀도 계산식(`len(links)/(len(words)/100)`)이 짧은 본문에서 과도하게 높은 비율로 계산.
- 조치:
  1. 최소 단어수 guard(예: 80단어 미만은 별도 규칙) 도입.
  2. 링크 밀도 기준을 절대값+비율 혼합으로 수정.
  3. 실제 정상 콘텐츠 샘플 5개로 회귀 테스트 추가.

## P0-3) `test_insight_extraction` 실패
- 점검 파일: `app/store/insights.py`, `app/tests/test_store_pack.py`
- 의심 원인:
  - 질문 추출에서 source filter와 count threshold 정책이 테스트 기대(1개)와 불일치.
- 조치:
  1. 질문 추출 정책 문서화(허용 source, min count).
  2. 구현/테스트 중 하나를 정책 기준으로 정렬.
  3. 같은 텍스트 중복 입력 시 dedup 테스트 추가.

---

## 4) A~F 기준 테스트 보강 로드맵

### A) MY_STORE 동기화
- 단위: 토큰 갱신, 페이지네이션, 상세 merge, 변경감지 hash.
- 통합: mock server로 200/429/5xx 재시도 시나리오.
- 회귀: 동일 데이터 재동기화 시 no-op 보장.

### B) AFFILIATE 인입
- CSV/시트 파서 테스트(인코딩, 헤더 오염, 중복 row).
- products upsert idempotency 테스트.
- sponsored 콘텐츠의 광고/제휴 문구 강제 테스트.

### C) Naver 패키지 생성
- 제목/본문/이미지 placeholder/표기/CTA/FAQ 필수 필드 검증 테스트.
- zip 내부 파일 존재성 + 스키마 검증 테스트.

### D) QA 게이트
- compliance + similarity + thin-content + unique-pack 통합 판정 테스트.
- 경계값 테스트(유사도 warn/reject 임계점).

### E) 상태머신
- 전이 테이블 전체 커버리지(허용/거부) 테스트.
- 재시작 복구(영속 저장 도입 후) 테스트.

### F) 트래킹
- 링크 파라미터 누락/중복/인코딩 테스트.
- 이벤트 중복 수집(idempotency key 도입 시) 테스트.
- 집계 지표 정확도 테스트(views/clicks/conversions/ctr/cvr).

---

## 5) CI 제안
- 단계 1: 빠른 단위 테스트(분당 실행).
- 단계 2: 통합 테스트(외부 API mock 포함).
- 단계 3: 릴리즈 전 스모크(패키지 생성 + 상태 전이 + 트래킹 집계).
- 실패 시 아티팩트(로그/중간 JSON/zip)를 업로드해 재현성 확보.

---

## 6) 추천 실행 커맨드
```bash
# Python 테스트
cd content_os
python -m unittest discover -s app/tests -p 'test_*.py'

# FastAPI 로컬 실행
uvicorn app.main:app --reload

# 샘플 체크리스트 실행
python scripts/run_seo_checklist.py
python scripts/run_naver_checklist.py

# 트래킹 집계 export
python scripts/export_metrics.py

# 프론트엔드 실행(루트)
cd ..
npm run dev
```
