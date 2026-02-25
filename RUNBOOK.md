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
