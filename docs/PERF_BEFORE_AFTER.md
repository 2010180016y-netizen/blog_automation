# PERF BEFORE / AFTER (측정 기반)

## 측정 범위
- 커머스 API 동기화 네트워크 I/O (`MyStoreSyncService.sync`)
- DB upsert 대량 처리 (`MyStoreRepository.batch_upsert_products`)
- 패키지 생성 파일 I/O (`NaverPackageGenerator.create_package`)

## 측정 커맨드
### 1) 동기화 before/after(동시성 설정 비교)
```bash
PYTHONPATH=content_os python - <<'PY'
import tempfile, os, time
from unittest.mock import MagicMock
import httpx
from app.store.my_store_sync import MyStoreRepository, MyStoreSyncService

def resp(payload):
    req=httpx.Request('GET','https://x')
    return httpx.Response(200,json=payload,request=req)

ids=[{'id':f'p{i}'} for i in range(40)]

def run(concurrency):
    tmp=tempfile.TemporaryDirectory(); db=os.path.join(tmp.name,'s.db')
    repo=MyStoreRepository(db)
    client=MagicMock()
    side=[resp({'access_token':'tok','expires_in':3600}), resp({'products':ids,'has_more':False})]
    side += [resp({'sku':f'S{i}','name':f'N{i}','price':i,'status':'ON'}) for i in range(40)]
    client.request.side_effect=side
    svc=MyStoreSyncService(repo=repo,client=client,concurrency=concurrency,max_retries=2,backoff_seconds=0.01)
    svc.token_url='https://auth'; svc.api_base_url='https://api'; svc.client_id='c'; svc.client_secret='s'
    t=time.perf_counter(); r=svc.sync(); elapsed=time.perf_counter()-t
    tmp.cleanup();
    return elapsed,r['timings']

b_elapsed,b_t=run(1)
a_elapsed,a_t=run(8)
print('baseline_elapsed',round(b_elapsed,4),b_t)
print('optimized_elapsed',round(a_elapsed,4),a_t)
PY
```

### 2) 패키지 I/O 중복 쓰기 회피 측정
```bash
PYTHONPATH=content_os python - <<'PY'
import tempfile
from app.publish.naver_package import NaverPackageGenerator

tmp=tempfile.TemporaryDirectory()
g=NaverPackageGenerator(output_root=tmp.name)
r1=g.create_package('perf_pkg','P1','MY_STORE','review','https://example.com/x',variant='A')
r2=g.create_package('perf_pkg','P1','MY_STORE','review','https://example.com/x',variant='A')
print('first_io',r1['io'],'render_sec',r1['render_sec'])
print('second_io',r2['io'],'render_sec',r2['render_sec'])
tmp.cleanup()
PY
```

## 측정 결과 (이번 실행)
### Sync benchmark
- baseline (concurrency=1)
  - elapsed: `0.0209s`
  - timings: `{'fetch_ids_sec': 0.000207, 'fetch_details_sec': 0.005637, 'db_upsert_enqueue_sec': 0.014874, 'total_sec': 0.020723}`
- optimized (concurrency=8)
  - elapsed: `0.0154s`
  - timings: `{'fetch_ids_sec': 0.000178, 'fetch_details_sec': 0.008884, 'db_upsert_enqueue_sec': 0.006158, 'total_sec': 0.015221}`

### Package I/O benchmark
- first build
  - `{'wrote_post_html': True, 'wrote_meta_json': True, 'write_sec': 0.000155}`
- second build (same input)
  - `{'wrote_post_html': False, 'wrote_meta_json': False, 'write_sec': 9.9e-05}`

## 성능 로그 예시
아래 로그는 런타임에서 출력되는 형태입니다.

```text
INFO my_store.token_fetch_sec=0.113
INFO my_store.fetch_ids_sec=0.324 count=240
INFO my_store.sync_sec=2.841 ids_sec=0.324 details_sec=1.912 db_sec=0.561 fetched=240 upserted=240 queued=57 errors=0
```

## 적용된 최적화 요약
1. **타이밍 로깅 추가(초 단위)**
   - token fetch / id fetch / detail fetch / db upsert+enqueue / total.
2. **동기화 안정화**
   - 동시성 제한(`Semaphore` + `ThreadPoolExecutor(max_workers=concurrency)`).
   - 재시도 + exponential backoff + 토큰 캐시.
3. **DB 병목 개선**
   - 배치 upsert chunk 처리 + 인덱스 추가(`product_id`, `payload_hash`, `refresh_queue(sku,status)`).
4. **파일 I/O 최소화**
   - 동일 파일 내용이면 재쓰기 생략(`_write_text_if_changed`, `_write_json_if_changed`).
