import json
import tempfile
import unittest
from pathlib import Path

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import (
    check_affiliate_disclosure_required,
    check_similarity_content,
    check_thin_content,
    check_unique_pack_required,
)
from scripts.import_affiliate_links import run_import_and_package


class TestAffiliateImport(unittest.TestCase):
    def test_import_and_package(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "aff.csv"
            csv_path.write_text(
                "partner_product_id,title,affiliate_link,category,keywords,content_type,source,usage_mode\n"
                "PT001,제휴상품,https://shoppingconnect.link/abc,가전,필터,review,shopping_connect,commercial\n",
                encoding="utf-8",
            )
            db_path = str(Path(td) / "blogs.db")
            res = import_affiliate_links_from_csv(db_path, str(csv_path))
            self.assertEqual(res["status"], "PASS")

            rows = [
                {
                    "partner_product_id": "PT001",
                    "title": "제휴상품",
                    "affiliate_link": "https://shoppingconnect.link/abc",
                }
            ]
            queue = create_content_queue_candidates(rows)
            self.assertGreaterEqual(len(queue), 2)
            pkg = generate_naver_affiliate_package(rows[0])
            qa = check_affiliate_disclosure_required(pkg)
            self.assertEqual(qa["status"], "PASS")
            thin = check_thin_content(pkg, min_text_chars=120)
            self.assertEqual(thin["status"], "PASS")
            self.assertIn("가격/혜택은 작성일 기준", pkg["html"])


    def test_fail_fast_on_reject_import(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "bad_aff.csv"
            csv_path.write_text(
                "partner_product_id,title,affiliate_link,category,keywords,content_type,source,usage_mode\n"
                "PT001,제휴상품,ftp://invalid-link,가전,필터,review,shopping_connect,commercial\n",
                encoding="utf-8",
            )
            out_dir = Path(td) / "out"
            db_path = str(Path(td) / "blogs.db")

            summary = run_import_and_package(db_path, str(csv_path), str(out_dir))

            self.assertEqual(summary["import"]["status"], "REJECT")
            self.assertEqual(summary["queue_count"], 0)
            self.assertEqual(summary["package_count"], 0)
            self.assertFalse((out_dir / "content_queue.json").exists())
            self.assertFalse((out_dir / "packages.json").exists())
            self.assertFalse((out_dir / "qa.json").exists())


    def test_similarity_reject(self):
        pkg = {
            "html": "<p>동일 문장 테스트 동일 문장 테스트 동일 문장 테스트 동일 문장 테스트</p>",
            "disclosure_required": False,
        }
        existing = ["동일 문장 테스트 동일 문장 테스트 동일 문장 테스트 동일 문장 테스트"]
        res = check_similarity_content(pkg, existing_contents=existing, warn_threshold=0.7, reject_threshold=0.8)
        self.assertEqual(res["status"], "REJECT")

    def test_unique_pack_required_reject_when_missing(self):
        res = check_unique_pack_required(None, require_unique_pack=True)
        self.assertEqual(res["status"], "REJECT")

    def test_run_import_and_package_reject_when_unique_pack_required(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "aff.csv"
            csv_path.write_text(
                "partner_product_id,title,affiliate_link,category,keywords,content_type,source,usage_mode\n"
                "PT001,제휴상품,https://shoppingconnect.link/abc,가전,필터,review,shopping_connect,commercial\n",
                encoding="utf-8",
            )
            db_path = str(Path(td) / "blogs.db")
            out_dir = Path(td) / "out"

            summary = run_import_and_package(
                db_path,
                str(csv_path),
                str(out_dir),
                require_unique_pack=True,
                unique_pack_results_by_sku={},
            )
            self.assertEqual(summary["import"]["status"], "PASS")
            qa = json.loads((out_dir / "qa.json").read_text(encoding="utf-8"))
            self.assertEqual(qa["schema_version"], "qa.v1")
            self.assertEqual(qa["items"][0]["status"], "REJECT")
            self.assertEqual(qa["items"][0]["checks"][-1]["code"], "UNIQUE_PACK_REQUIRED")
            self.assertTrue((out_dir / "qa_archive").exists())


    def test_qa_json_schema_and_archive(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "aff.csv"
            csv_path.write_text(
                "partner_product_id,title,affiliate_link,category,keywords,content_type,source,usage_mode\n"
                "PT001,제휴상품,https://shoppingconnect.link/abc,가전,필터,review,shopping_connect,commercial\n",
                encoding="utf-8",
            )
            db_path = str(Path(td) / "blogs.db")
            out_dir = Path(td) / "out"

            run_import_and_package(db_path, str(csv_path), str(out_dir))
            qa = json.loads((out_dir / "qa.json").read_text(encoding="utf-8"))
            self.assertEqual(qa["schema_version"], "qa.v1")
            self.assertIn("generated_at", qa)
            self.assertIn("summary", qa)
            self.assertEqual(qa["summary"]["total"], 1)
            self.assertIn("items", qa)
            self.assertEqual(len(qa["items"]), 1)
            archives = list((out_dir / "qa_archive").glob("qa_*.json"))
            self.assertGreaterEqual(len(archives), 1)

    def test_thin_content_reject(self):
        bad_pkg = {"html": "<h1>짧은글</h1>", "disclosure_required": True}
        res = check_thin_content(bad_pkg, min_text_chars=50)
        self.assertEqual(res["status"], "REJECT")


if __name__ == "__main__":
    unittest.main()
