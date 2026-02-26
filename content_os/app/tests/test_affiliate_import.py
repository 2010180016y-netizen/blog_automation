import json
import tempfile
import unittest
from pathlib import Path

from app.content.naver.generator import generate_naver_affiliate_package
from app.ingest.affiliate_sc.importer import create_content_queue_candidates, import_affiliate_links_from_csv
from app.qa.compliance import check_affiliate_disclosure_required


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
            self.assertIn("가격/혜택은 작성일 기준", pkg["html"])


if __name__ == "__main__":
    unittest.main()
