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


---

## 7) 수익화 P0 기능 테스트 플랜 (추가)

## 7.1 상품 SSOT + Admin
- 단위 테스트
  - 상품 우선순위 정렬, 제외 플래그 필터링, soft-delete 복구
- 통합 테스트
  - 커머스API/제휴 ingest 후 SSOT 일관성 검증
  - 운영자 override가 자동 동기화 결과를 덮어쓰는지 검증
- 회귀 테스트
  - 동일 SKU 재동기화 시 idempotent update

## 7.2 콘텐츠-상품 매칭 엔진
- 단위 테스트
  - intent rule 매핑(info/compare/review/buy) 정확성
  - 룰 미충족 시 fallback 선택 검증
- 통합 테스트
  - 콘텐츠 생성 요청→매칭→템플릿 선택→패키지 생성 E2E
- 데이터 품질 테스트
  - 의도 분포 급변(drift) 탐지 경보

## 7.3 가격/혜택 변동 대응
- 단위 테스트
  - 변동 고지 문구 자동 삽입 여부
  - 작성일/업데이트일/가격확인일 자동 표기
- 통합 테스트
  - 가격 변경 이벤트 발생 시 refresh 큐 등록 및 본문 재렌더 트리거
- 정책 테스트
  - 고정 가격 숫자 하드코딩 탐지 lint

## 7.4 CRO 템플릿 강제
- 단위 테스트
  - 추천/비추천, 체크리스트, 비교표, FAQ 누락 시 QA REJECT
- 통합 테스트
  - 템플릿 충족 콘텐츠만 READY 전이 허용

## 7.5 A/B 최소 프레임
- 단위 테스트
  - variant 배정 안정성(동일 사용자 동일 variant)
  - `exp_id`, `variant` 이벤트 스키마 검증
- 통합 테스트
  - CTA 문구/위치/표/리드문 2안 실험 지표 집계 검증
- 통계 테스트
  - 최소 샘플 도달 전 승자 확정 금지

---

## 8) 운영 릴리즈 체크리스트 (수익화 관점)
1. SSOT 상품 중 "우선순위/제외" 미설정 비율이 10% 이하인가?
2. 최근 24시간 내 가격 확인률이 95% 이상인가?
3. 실험 이벤트(`exp_id`, `variant`) 누락률이 0.5% 이하인가?
4. CRO 필수 블록 누락으로 REJECT된 건이 주간 감소 추세인가?
5. intent별 CTR/CVR가 대시보드에서 분리 관측 가능한가?


---

## 9) P1 성장 기능 테스트 플랜 (추가)

## 9.1 클러스터 자동 생성(허브-스포크)
- 단위 테스트
  - 허브/스포크 생성 규칙, 내부링크 삽입 규칙, 앵커텍스트 충돌 처리
- 통합 테스트
  - 허브 생성→스포크 생성→내부링크 연결→색인 체크리스트 E2E
- 품질 테스트
  - orphan 페이지 비율, 순환 링크 비율, 클릭 심도 개선 검증

## 9.2 성과기반 콘텐츠 리프레시
- 단위 테스트
  - refresh score 산식(traffic/conversion/freshness) 정확성
- 통합 테스트
  - 점수 상위 글 자동 큐잉→FAQ/비교표 갱신→재발행 파이프라인
- 회귀 테스트
  - 동일 입력 점수 재계산 안정성(결정성)

## 9.3 리텐션(이메일/카카오/푸시)
- 단위 테스트
  - 옵트인/해지/동의 버전 관리
  - 이벤트 트리거 매핑(가격변동/재입고/업데이트)
- 통합 테스트
  - 트리거 이벤트→메시지 발송→클릭→재방문/전환 집계 E2E
- 컴플라이언스 테스트
  - 동의 없는 대상 발송 차단, 해지 후 즉시 차단 검증

## 9.4 비교표/추천표 자동 생성
- 단위 테스트
  - SSOT 필드 누락/형식오류 시 안전한 fallback
  - 가격/특징/추천대상/주의점 컬럼 완전성 검증
- 통합 테스트
  - SSOT 변경 발생 시 표 diff 및 재렌더 반영
- SEO 테스트
  - 표 포함 페이지의 체류/스크롤/클릭 이벤트 수집 검증

## 9.5 UGC 수집/권리/검수
- 단위 테스트
  - 권리동의 필수 필드 미입력 시 REJECT
  - 금칙어/개인정보 마스킹 규칙
- 통합 테스트
  - 제출→권리검증→검수승인→게시까지 상태머신 E2E
- 감사 추적 테스트
  - 누가/언제/어떤 동의버전으로 승인했는지 이력 재현

---

## 10) 성장 기능 릴리즈 게이트
1. 허브-스포크 내부링크 자동 연결 성공률 98% 이상
2. 리프레시 큐 처리 지연(TTR) p95가 48시간 이하
3. 리텐션 메시지 이벤트 유실률 1% 이하
4. 비교표 최신화 지연 24시간 이하
5. UGC 권리검증 실패 건이 게시 경로로 누수되지 않을 것(0건)


---

## 11) P2 광고 수익화 테스트 플랜 (추가)

## 11.1 광고 배치 룰 엔진
- 단위 테스트
  - CTA/버튼/입력 주변 금지 구역 규칙 검증
  - 광고 슬롯 과밀도/반복 노출 규칙 검증
- 통합 테스트
  - 페이지 렌더→광고 린트→QA 게이트 연동 E2E
- 회귀 테스트
  - 기존 정상 템플릿에서 false positive 증가 방지

## 11.2 우발 클릭 방지 시각 검사
- 단위 테스트
  - bbox 거리 계산/임계치 판정 정확성
- 통합 테스트
  - 모바일/데스크톱 뷰포트별 슬롯 안전성 검증
- 아티팩트 테스트
  - 위반 케이스 스크린샷 자동 보관 및 재현 가능성

## 11.3 RPM 실험 프레임
- 단위 테스트
  - variant 할당 일관성, 트래픽 분배 균등성
- 통합 테스트
  - 광고 슬롯 레이아웃 변경→이벤트 수집→RPM 집계 E2E
- 통계 테스트
  - 최소 샘플 충족 전 승자 확정 금지

## 11.4 ads.txt 자동 점검/배포
- 단위 테스트
  - ads.txt 라인 파서/검증기
- 통합 테스트
  - 배포 후 도메인 fetch 검증, mismatch 시 롤백
- 운영 테스트
  - 다중 도메인 동시 배포 시 부분 실패 격리

---

## 12) 광고 수익화 릴리즈 게이트
1. 금지 구역 위반 광고 슬롯 0건
2. 시각 검사 기준 미달 슬롯 0건
3. RPM 실험 이벤트 누락률 1% 이하
4. ads.txt 검증 통과율 100%
5. 정책 안전성 경고가 있는 빌드는 배포 금지
