import json
import os

import pytest

from app.publish.naver_package import NaverPackageGenerator
from app.qa.gate import QAGate, QAGateInput
from app.store.my_store_sync import MyStoreRepository, MyStoreSyncService
from http_mocking import build_mock_client


@pytest.fixture
def qa_content_data():
    return {
        "intent": "review",
        "section_titles": [
            "사용법",
            "공식(근거)",
            "예시",
            "추천 대상 / 비추천 대상",
            "구매 전 체크리스트",
            "경쟁/대체 옵션 비교표",
            "FAQ",
            "주의사항",
            "엣지케이스",
        ],
        "faq_count": 6,
        "example_count": 1,
        "caution_count": 1,
        "image_count": 3,
        "unique_fact_count": 2,
    }


def test_sync_to_qa_to_package_flow(tmp_path, qa_content_data):
    db_path = str(tmp_path / "sync.db")
    out_root = str(tmp_path / "packages")

    repo = MyStoreRepository(db_path=db_path)
    routes = {
        ("POST", "https://auth.example.com/token"): (200, {"access_token": "tok", "expires_in": 3600}),
        ("GET", "https://api.example.com/products?page_size=50&page=1"): (
            200,
            {"products": [{"id": "p1"}, {"id": "p2"}], "has_more": False},
        ),
        ("GET", "https://api.example.com/products/p1"): (
            200,
            {"sku": "S1", "name": "N1", "price": 10000, "status": "ON"},
        ),
        ("GET", "https://api.example.com/products/p2"): (
            200,
            {"sku": "S2", "name": "N2", "price": 20000, "status": "ON"},
        ),
    }

    client = build_mock_client(routes)
    svc = MyStoreSyncService(repo=repo, client=client, concurrency=2, max_retries=1, backoff_seconds=0.01)
    svc.token_url = "https://auth.example.com/token"
    svc.api_base_url = "https://api.example.com"
    svc.client_id = "cid"
    svc.client_secret = "sec"

    result = svc.sync()

    assert result["fetched"] == 2
    assert result["upserted"] == 2
    assert "timings" in result
    assert result["timings"]["total_sec"] >= 0

    gate = QAGate()
    report = gate.evaluate(
        QAGateInput(
            content="[제휴] 제품 스펙과 사용시 주의사항을 기반으로 실사용 관점에서 정리합니다.",
            language="ko",
            source_type="AFFILIATE",
            content_data=qa_content_data,
        )
    )
    assert report["status"] == "PASS", report

    generator = NaverPackageGenerator(output_root=out_root)
    package = generator.create_package(
        content_id="C-FLOW-1",
        product_id="P-FLOW-1",
        source_type="AFFILIATE",
        intent="review",
        cta_link="https://example.com/p-flow",
        variant="A",
    )

    assert package["status"] == "PASS", package
    assert os.path.exists(package["post_html"])
    assert os.path.exists(package["meta_json"])

    with open(package["meta_json"], "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["variant"] == "A"


def test_sync_failure_logs_are_actionable(tmp_path, caplog):
    db_path = str(tmp_path / "sync.db")
    repo = MyStoreRepository(db_path=db_path)
    routes = {
        ("POST", "https://auth.example.com/token"): (200, {"access_token": "tok", "expires_in": 3600}),
        ("GET", "https://api.example.com/products?page_size=50&page=1"): (
            200,
            {"products": [{"id": "p1"}], "has_more": False},
        ),
        ("GET", "https://api.example.com/products/p1"): (500, {"detail": "boom"}),
    }

    client = build_mock_client(routes)
    svc = MyStoreSyncService(repo=repo, client=client, concurrency=1, max_retries=0)
    svc.token_url = "https://auth.example.com/token"
    svc.api_base_url = "https://api.example.com"
    svc.client_id = "cid"
    svc.client_secret = "sec"

    with caplog.at_level("ERROR"):
        result = svc.sync()

    assert result["errors"] == 1
    assert any("check API auth/rate-limit/payload" in rec.message for rec in caplog.records)
