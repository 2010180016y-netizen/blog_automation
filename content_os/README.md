# Content Compliance Rule Engine

Part of the Content-Commerce OS.

## Features
- Multi-language support (KO/EN)
- Rule-based detection for banned claims
- Disclosure requirement checks
- YMYL section validation
- Pattern-based efficacy claim detection

## Usage
### API
```bash
uvicorn app.main:app --reload
```

### CLI
```bash
python -m app.eval.compliance --file content.txt --lang ko
```

## Local test-first in restricted networks

If `pip install -e ./content_os` fails in offline/proxy-restricted environments, run tests directly first:

```bash
cd content_os
python -m pytest -q
```

## Offline packaging (proxy-restricted environments)

### 1) On a connected machine, prebuild wheels
```bash
cd content_os
python -m pip install --upgrade pip wheel
python -m pip wheel -r requirements-lock.txt -w ./wheelhouse
```

### 2) Move artifacts to restricted environment
- Copy `content_os/wheelhouse/`
- Copy `content_os/requirements-lock.txt`

### 3) Install without internet
```bash
cd content_os
python -m pip install --no-index --find-links=./wheelhouse -r requirements-lock.txt
```

### 4) Fallback: run tests without editable install
```bash
cd content_os
python -m pytest -q
```


## Sitemap/RSS generation + indexing status monitoring

```bash
python scripts/manage_indexing_feeds.py \
  --site-url https://example.com \
  --db-path ../blogs.db \
  --out-dir ./out/feeds \
  --google-status-json ./ops/google_sitemap_status.json \
  --naver-status-json ./ops/naver_sitemap_status.json \
  --robots-txt ./ops/robots.txt
```

This generates `sitemap.xml` and `rss.xml`, then evaluates Google/Naver submission status files and robots directives into a single JSON report.


## Search Console + Naver operations dashboard

```bash
python scripts/generate_ops_dashboard.py \
  --query-json ./ops/query_rows.json \
  --page-json ./ops/page_rows.json \
  --conversion-json ./ops/conversions.json \
  --current-index-json ./ops/current_index_status.json \
  --previous-index-json ./ops/previous_index_status.json
```

The script outputs a JSON operations report for CTR issues, indexing error deltas, conversion leak flags, and refresh priorities.


## Product feed + Merchant Center integration

```bash
python scripts/generate_merchant_assets.py \
  --db-path ../blogs.db \
  --site-url https://example.com \
  --out-dir ./out/merchant \
  --snapshot-path ./out/merchant/product_snapshot.json
```

This command generates:
- Merchant Center feed (`merchant_feed.xml`)
- Product/merchant listing JSON-LD files (`jsonld/<SKU>.json`)
- Change detection report for price/inventory/shipping/link deltas (`new/changed/removed`)


## Ads infra: ads.txt + accidental-click prevention

### 1) Generate/validate/deploy `ads.txt`

Prepare seller records JSON:

```json
[
  {"domain":"google.com","publisher_id":"pub-xxxxxxxx","relationship":"DIRECT","cert_authority_id":"f08c47fec0942fa0"},
  {"domain":"example-ssp.com","publisher_id":"account-123","relationship":"RESELLER"}
]
```

Then run:

```bash
python scripts/manage_ads_txt.py \
  --records-json ./ops/ads_sellers.json \
  --output-path ./out/ads/ads.txt \
  --expected-domain google.com
```

Optional production verification:

```bash
python scripts/manage_ads_txt.py \
  --records-json ./ops/ads_sellers.json \
  --output-path ./out/ads/ads.txt \
  --validate-url https://example.com/ads.txt
```

### 2) Ads UX linter hardening

`app.ads.linter.AdsLinter` now rejects ad units that are too close to CTA/input/select/player controls and flags interactive controls inside ad containers.

### 3) RPM/RPS guardrail experiment

Use `app.ads.experiment.recommend_ad_experiment(...)` to keep monetization tests incremental (`INCREASE_STEP`/`HOLD`/`DECREASE`) based on RPM, RPS, ad density, and bounce-rate guardrails.


## Disclosure automation (KO/EN sponsorship & affiliate)

Use ruleset-driven disclosure insertion when `disclosure_required=true`:

```bash
python scripts/apply_disclosures.py \
  --title "Best Air Purifier Review" \
  --content-file ./ops/draft.txt \
  --language en \
  --disclosure-required \
  --output-file ./ops/draft_with_disclosure.txt
```

Behavior:
- Inject title/body disclosure templates from `app/rules/compliance_rules.v1.yaml`
- Add clear disclosure text near affiliate links
- Compliance QA rejects missing intro disclosure or missing nearby affiliate-link disclosure


## Image SEO auto-optimization (alt/capacity/format)

`UniquePackGenerator` now performs image SEO preprocessing:
- image resize + WebP conversion (Pillow available 환경) with fallback copy mode
- optimization report output (`image_optimization_report.json`)
- descriptive alt-text generation (description-first)
- keyword-stuffing detection on alt text (spam guardrail)

For HTML rendering, apply lazy-loading attrs (`loading=lazy`, `decoding=async`) via `app.pipeline.image_seo.apply_lazy_loading_to_html(...)`.


## Internal link validator (orphan detection + crawler simulation)

Build recommendations and validation outputs:

```bash
python scripts/build_internal_links.py
```

Or validate your own post graph:

```bash
python scripts/validate_internal_links.py \
  --posts-json ./ops/posts.json \
  --start-slug home \
  --max-depth 3
```

Validation report includes:
- orphan pages (inbound link 0)
- crawler-reachable pages from seed URLs
- anchor quality issues (too-short anchor text)


## Core Web Vitals monitoring + alerts

Run CWV budget checks by page type (landing/review/comparison) and regression alerts:

```bash
python scripts/monitor_cwv.py \
  --current-json ./ops/cwv_current.json \
  --previous-json ./ops/cwv_previous.json \
  --webhook-url https://hooks.slack.com/services/xxx/yyy/zzz
```

Supports:
- per-page-type performance budget (`lcp`, `inp`, `cls`, `ttfb`)
- regression detection vs previous snapshot
- probable cause breakdown (`image`, `ad_script`, `plugin`) for alert triage


## SmartStore SSOT sync via Commerce API

Build your product SSOT from official Naver Commerce API flow:
1. `POST /v1/products/search` (list)
2. `GET /v2/products/channel-products/{channelProductNo}` and/or `GET /v2/products/origin-products/{originProductNo}` (detail enrichment)

```bash
python scripts/sync_commerce_ssot.py \
  --base-url https://api.commerce.naver.com \
  --token <ACCESS_TOKEN> \
  --db-path ../blogs.db \
  --page 1 --size 100
```

This upserts into `products_ssot` table and can optionally dump rows to JSON for Google Sheet bridge workflows.


## Two-track product data strategy (safe monetization)

For sustainable automation, separate product sources:
- **Track A (own products)**: SmartStore Commerce API SSOT (`products_ssot`)
- **Track B (third-party products)**: Shopping Connect partner links (`partner_products`)

Do **not** treat Shopping Search/OpenAPI result pools as commercial SSOT source.

Sync partner products + merge two-track SSOT:

```bash
python scripts/sync_partner_products.py \
  --db-path ../blogs.db \
  --partner-json ./ops/shopping_connect_products.json \
  --out-json ./out/two_track_ssot.json
```

The sync enforces source validation (commercial use of `shopping_search_api`/`naver_shopping_openapi` is rejected) and exports merged rows (`own_store` + `partner_store`).


## Unified products table (2-source merge with source_type)

Merge two sources into a single `products` SSOT table with typed provenance:
- `source_type=MY_STORE` (Commerce API sync)
- `source_type=AFFILIATE_SHOPPING_CONNECT` (Shopping Connect link SSOT)
- optional: `source_type=MY_BRANDSTORE_ANALYTICS`

```bash
python scripts/sync_unified_products.py \
  --db-path ../blogs.db \
  --refresh-queue-path ./out/refresh_queue.json
```

Rules implemented:
- `MY_STORE`: price/shipping/link change detection -> refresh queue (`refresh_queue.json`)
- `AFFILIATE_SHOPPING_CONNECT`: link is SSOT, price left nullable, default disclaimer inserted ("가격/혜택은 변동될 수 있습니다...")


## P0/P1 data modules (requested setup)

### P0-1) MY_STORE sync (Commerce API)
Already supported via `scripts/sync_commerce_ssot.py` (`/v1/products/search` + `/v2` detail enrichment).

### P0-2) AFFILIATE Shopping Connect ingest
Use Shopping Connect link list from JSON/CSV/Google Sheet CSV and ingest safely:

```bash
python scripts/sync_partner_products.py \
  --db-path ../blogs.db \
  --partner-csv ./ops/shopping_connect_links.csv \
  --out-json ./out/two_track_ssot.json
```

Input guardrails:
- source must be `shopping_connect`
- valid HTTP(S) affiliate link required
- `content_type` mapping enforced (`landing/review/comparison/shorts`)
- disallowed/private scraping-style sources are rejected by design

### P1) MY_BRANDSTORE_ANALYTICS summary
When brandstore bizdata stats are available:

```bash
python scripts/summarize_brandstore_stats.py --stats-json ./ops/brandstore_stats.json
```


## Prompt-implementation modules (MY_STORE + AFFILIATE_SC)

- MY_STORE robust sync modules:
  - `app/ingest/naver_commerce/client.py` (OAuth2 + retry/rate-limit/token-refresh)
  - `app/ingest/naver_commerce/products.py` (list->detail enrichment, graceful parse fail)
  - `app/ingest/naver_commerce/sync.py` (DB upsert + refresh queue)
  - `scripts/sync_my_store.py`

- AFFILIATE_SC modules:
  - `app/ingest/affiliate_sc/importer.py` (CSV import + queue candidates)
  - `app/content/naver/{templates.py,generator.py}` (html+image slot+CTA+disclosure+FAQ)
  - `app/qa/compliance.py` (disclosure required => REJECT)
  - `scripts/import_affiliate_links.py`
