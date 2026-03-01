#!/usr/bin/env python3
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_OS = os.path.join(ROOT, "content_os")
if CONTENT_OS not in sys.path:
    sys.path.insert(0, CONTENT_OS)

from app.store.my_store_sync import MyStoreRepository, MyStoreSyncService


def main() -> int:
    db_path = os.getenv("MY_STORE_DB_PATH", os.path.join(CONTENT_OS, "blogs.db"))
    repo = MyStoreRepository(db_path=db_path)
    service = MyStoreSyncService(repo=repo)
    result = service.sync()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
