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
