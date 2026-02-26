import tempfile
import unittest
from pathlib import Path

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import check_affiliate_disclosure_required, check_thin_content
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

    def test_thin_content_reject(self):
        bad_pkg = {"html": "<h1>짧은글</h1>", "disclosure_required": True}
        res = check_thin_content(bad_pkg, min_text_chars=50)
        self.assertEqual(res["status"], "REJECT")


if __name__ == "__main__":
    unittest.main()
