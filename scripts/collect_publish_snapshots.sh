#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:3000}"
WP_URL="${WP_URL:-http://127.0.0.1:18080}"
WP_USER="${WP_USER:-user}"
WP_PASS="${WP_PASS:-pass}"
BLOG_ID="${BLOG_ID:-1}"
OUT_DIR="${OUT_DIR:-./publish_e2e_snapshots}"

mkdir -p "$OUT_DIR"

echo "Collecting publish snapshots into $OUT_DIR"

# invalid id
curl -sS -o "$OUT_DIR/publish_invalid_id.json" -w "%{http_code}" \
  -X POST "$BASE_URL/api/blogs/publish" \
  -H 'Content-Type: application/json' \
  -d "{\"id\":9999999,\"wpUrl\":\"$WP_URL\",\"wpUser\":\"$WP_USER\",\"wpPass\":\"$WP_PASS\",\"status\":\"draft\"}" \
  > "$OUT_DIR/publish_invalid_id.status"

# valid id + statuses
for st in draft future publish; do
  curl -sS -o "$OUT_DIR/publish_${st}.json" -w "%{http_code}" \
    -X POST "$BASE_URL/api/blogs/publish" \
    -H 'Content-Type: application/json' \
    -d "{\"id\":$BLOG_ID,\"wpUrl\":\"$WP_URL\",\"wpUser\":\"$WP_USER\",\"wpPass\":\"$WP_PASS\",\"status\":\"$st\"}" \
    > "$OUT_DIR/publish_${st}.status"
done

echo "Done. Generated files:"
ls -1 "$OUT_DIR"
