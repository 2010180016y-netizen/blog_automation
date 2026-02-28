# Unified Runbook (Node + Python + Publishing + SEO + CI)

## 0) Environment variables
Create `.env.local` from `.env.example` at repo root.

Required/important keys:
- `GEMINI_API_KEY`
- `APP_URL`
- `WP_ALLOWED_HOSTS` (optional allowlist for WP publishing)
- `PUBLISH_QUEUE_DB_PATH` (optional, default `publish_queue.db`)
- `PUBLISH_E2E_LOG_PATH` (optional evidence log file)
- `PUBLISH_E2E_MODE` (optional evidence tag: `mock`/`staging`)

## 1) Node app boot
```bash
npm ci
npm run lint
npm run dev
```

Health-style check:
```bash
curl -i http://127.0.0.1:3000/api/blogs
```

## 2) Python tests/API
```bash
python -m pytest -q
cd content_os
uvicorn app.main:app --reload
```

Health:
```bash
curl -i http://127.0.0.1:8000/health
```

## 3) Publishing (WordPress)
### 3.1 Queue API (durable SQLite-backed)
```bash
curl -X POST http://127.0.0.1:8000/publish/enqueue \
  -H 'Content-Type: application/json' \
  -d '{"content_id":"POST001","data":{"platform":"naver"}}'

curl -X POST http://127.0.0.1:8000/publish/transition \
  -H 'Content-Type: application/json' \
  -d '{"content_id":"POST001","next_state":"QA_PASS"}'
```

### 3.2 WP publish snapshots (mock/staging)
```bash
BASE_URL=http://127.0.0.1:3000 \
WP_URL=http://127.0.0.1:18080 \
BLOG_ID=1 \
OUT_DIR=./publish_e2e_snapshots \
./scripts/collect_publish_snapshots.sh
```

## 4) Naver package generation
Use `content_os/app/publish/naver_package.py` integration path from app/services.
(Operational upload step is Human-in-the-loop.)

## 5) SEO eligibility checks
### URL-based check
```bash
python content_os/scripts/run_seo_checklist.py --url https://example.com/post
```

### Local HTML check
```bash
python content_os/scripts/run_seo_checklist.py --html-file ./sample.html --robots true --sitemap true --search-console true
```

## 6) CI parity
CI workflow runs:
- `npm ci`
- `npm run lint`
- `pip install -e ./content_os`
- `python -m pytest -q` (working-directory: `content_os`)

Local parity command:
```bash
npm run lint && python -m pytest -q
```


## 7) Sitemap + RSS generation and indexing monitoring (Google/Naver)
```bash
python content_os/scripts/manage_indexing_feeds.py \
  --site-url https://example.com \
  --db-path ./blogs.db \
  --out-dir ./content_os/out/feeds \
  --google-status-json ./ops/google_sitemap_status.json \
  --naver-status-json ./ops/naver_sitemap_status.json \
  --robots-txt ./ops/robots.txt \
  --webhook-url https://hooks.slack.com/services/xxx/yyy/zzz
```

- 출력: sitemap.xml/rss.xml 생성 + 상태 모니터링 PASS/WARN/FAIL JSON
- `google-status-json`/`naver-status-json`가 없으면 `UNVERIFIED`로 표기됩니다.


## 8) Search Console + Naver operations dashboard/alerts
```bash
python content_os/scripts/generate_ops_dashboard.py \
  --query-json ./ops/query_rows.json \
  --page-json ./ops/page_rows.json \
  --conversion-json ./ops/conversions.json \
  --current-index-json ./ops/current_index_status.json \
  --previous-index-json ./ops/previous_index_status.json
```

Report contains:
- low-CTR keyword detection + title/meta A/B candidates
- indexing error increase alerts
- high-rank / low-conversion page flags
- refresh priority list


## 9) Product feed + Merchant Center asset generation
```bash
python content_os/scripts/generate_merchant_assets.py \
  --db-path ./blogs.db \
  --site-url https://example.com \
  --out-dir ./content_os/out/merchant \
  --snapshot-path ./content_os/out/merchant/product_snapshot.json
```

Outputs:
- `merchant_feed.xml` (Merchant Center feed)
- `jsonld/*.json` (Product/merchant listing JSON-LD)
- `changes` report (`new/changed/removed`) for scheduler-triggered refresh


## 10) Ads infra operations (`ads.txt` + UX policy guardrails)

### Generate + validate + deploy-ready ads.txt
```bash
python content_os/scripts/manage_ads_txt.py \
  --records-json ./ops/ads_sellers.json \
  --output-path ./content_os/out/ads/ads.txt \
  --expected-domain google.com
```

(옵션) 라이브 사이트 점검
```bash
python content_os/scripts/manage_ads_txt.py \
  --records-json ./ops/ads_sellers.json \
  --output-path ./content_os/out/ads/ads.txt \
  --validate-url https://example.com/ads.txt
```

### 광고 UX 정책 점검
- `AdsLinter`는 버튼/입력/드롭다운/플레이어 등 클릭 요소 근접 배치를 차단
- ad 컨테이너 내부에 상호작용 요소가 있으면 우발 클릭 위험으로 거부

### RPM/RPS 기반 실험 규칙
- `recommend_ad_experiment(rpm, rps, ads_per_page, bounce_rate)`로 `INCREASE_STEP/HOLD/DECREASE` 권고
- bounce rate가 높거나 ad density cap 도달 시 증량 금지


## 11) Global traffic consent baseline (EEA/UK/CH)

WordPress `content-os-seo` plugin now includes a minimal CMP + Google Consent Mode bridge:
- Target region request headers (`CF-IPCountry`/`GEOIP_COUNTRY_CODE`/`X-Country-Code`) in EEA/UK/CH default to denied storage.
- Consent banner allows Accept/Reject and updates `gtag('consent', 'update', ...)`.
- Consent state is persisted in `cos_consent_v1` (localStorage + cookie).

Optional customization via WP filters:
- `cos_seo_consent_enabled`
- `cos_seo_consent_regions`


## 12) 추천/후기/제휴 표기 자동화 (KO/EN)

```bash
python content_os/scripts/apply_disclosures.py \
  --title "Best Air Purifier Review" \
  --content-file ./ops/draft.txt \
  --language en \
  --disclosure-required \
  --output-file ./ops/draft_with_disclosure.txt
```

동작:
- 룰셋(`content_os/app/rules/compliance_rules.v1.yaml`) 기반 제목/본문 상단 표기 자동 삽입
- 제휴 링크 주변에 눈에 띄는 Disclosure 문구 자동 삽입
- QA/컴플라이언스에서 표기 누락 시 `REJECT`


## 13) 이미지 SEO 자동 최적화 (alt/용량/포맷)

`UniquePackGenerator` 처리 시 자동으로:
- 리사이즈 + WebP 변환(가능 환경)
- 이미지 최적화 리포트 저장 (`image_optimization_report.json`)
- 설명 중심 alt 텍스트 생성
- alt 키워드 스터핑 감지(스팸 방지)

HTML 본문 `<img>`에는 `loading="lazy"`, `decoding="async"`를 적용해 렌더링 비용을 줄입니다(`app.pipeline.image_seo.apply_lazy_loading_to_html`).


## 14) 내부링크 검증기 (오펀 페이지 + 크롤러 시뮬레이션)

권장 링크 생성 + 검증 리포트 생성:
```bash
python content_os/scripts/build_internal_links.py
```

실데이터 검증:
```bash
python content_os/scripts/validate_internal_links.py \
  --posts-json ./ops/posts.json \
  --start-slug home \
  --max-depth 3
```

리포트 핵심:
- 오펀 페이지(`orphans`)
- 시작 URL 기준 크롤 도달 페이지(`crawl.visited`)
- 앵커 텍스트 품질 이슈(`anchor_issues`)


## 15) Core Web Vitals 모니터링 + 자동 경보

```bash
python content_os/scripts/monitor_cwv.py \
  --current-json ./ops/cwv_current.json \
  --previous-json ./ops/cwv_previous.json \
  --webhook-url https://hooks.slack.com/services/xxx/yyy/zzz
```

기능:
- 페이지 유형별 성능 예산(landing/review/comparison) 평가
- 성능 악화(regression) 자동 탐지
- 원인 분해(이미지/광고 스크립트/플러그인) 기반 경보 payload 생성


## 16) SmartStore SSOT 구축 (Commerce API 정석 플로우)

표준 동기화 패턴:
- `POST /v1/products/search`로 목록 조회
- 목록의 `channelProductNo`/`originProductNo`를 사용해
  - `GET /v2/products/channel-products/{...}`
  - `GET /v2/products/origin-products/{...}`
  로 상세 보강

실행:
```bash
python content_os/scripts/sync_commerce_ssot.py \
  --base-url https://api.commerce.naver.com \
  --token <ACCESS_TOKEN> \
  --db-path ./blogs.db \
  --page 1 --size 100
```

결과:
- `products_ssot` 테이블 upsert (글 생성/검수/발행의 단일 원천 데이터)
- 필요 시 `--out-json`으로 시트 연동(구글시트) 파이프라인에 전달 가능


## 17) 2트랙 상품 데이터 운영 (내 상품 + 제휴 상품)

안전한 구조:
- Track A: 내 스토어 상품 = Commerce API 기반 `products_ssot`
- Track B: 외부 상품 = Shopping Connect 링크 기반 `partner_products`

주의:
- `shopping_search_api`/`naver_shopping_openapi` 결과를 상업적 SSOT로 직접 사용하지 않음(정책 리스크)

실행:
```bash
python content_os/scripts/sync_partner_products.py \
  --db-path ./blogs.db \
  --partner-json ./ops/shopping_connect_products.json \
  --out-json ./content_os/out/two_track_ssot.json
```

결과:
- 정책 검증 통과 데이터만 `partner_products` upsert
- `own_store + partner_store` 통합 SSOT json 생성


## 18) 두 데이터 소스 통합(products + source_type)

단일 상품 테이블 `products`로 통합:
- `MY_STORE` (커머스API 동기화)
- `AFFILIATE_SHOPPING_CONNECT` (쇼핑 커넥트 링크 기반)
- (옵션) `MY_BRANDSTORE_ANALYTICS`

실행:
```bash
python content_os/scripts/sync_unified_products.py \
  --db-path ./blogs.db \
  --refresh-queue-path ./content_os/out/refresh_queue.json
```

운영 규칙:
- `MY_STORE`: 가격/옵션/배송/링크 변경 감지 시 리프레시 큐 자동 생성
- `AFFILIATE_SHOPPING_CONNECT`: 링크를 SSOT로 사용, 가격은 nullable 유지 +
  "가격/혜택은 변동될 수 있음(작성일 기준)" 고지 자동 삽입


## 19) P0/P1 추가 모듈 운영 가이드

### P0-1) MY_STORE (커머스API)
- `sync_commerce_ssot.py` 사용 (목록 + 상세 보강).

### P0-2) AFFILIATE (Shopping Connect 링크 인입)
JSON/CSV/구글시트 CSV 입력 지원:

```bash
python content_os/scripts/sync_partner_products.py \
  --db-path ./blogs.db \
  --partner-csv ./ops/shopping_connect_links.csv \
  --out-json ./content_os/out/two_track_ssot.json
```

검증 항목:
- source=`shopping_connect`
- 링크 유효성(HTTP/HTTPS)
- 카테고리/키워드/콘텐츠 타입 매핑(`landing/review/comparison/shorts`)
- 비공개/내부 API, 캡차 우회 방식은 설계에서 배제

### P1) MY_BRANDSTORE_ANALYTICS (해당 시)
```bash
python content_os/scripts/summarize_brandstore_stats.py \
  --stats-json ./ops/brandstore_stats.json
```


## 20) Prompt implementation quick-run

### MY_STORE robust sync
```bash
python content_os/scripts/sync_my_store.py \
  --base-url https://api.commerce.naver.com \
  --client-id <id> \
  --client-secret <secret> \
  --db-path ./blogs.db
```

### AFFILIATE_SC import + Naver package generation
```bash
python content_os/scripts/import_affiliate_links.py \
  --db-path ./blogs.db \
  --csv-path ./ops/shopping_connect_links.csv \
  --out-dir ./content_os/out/affiliate_packages
```
