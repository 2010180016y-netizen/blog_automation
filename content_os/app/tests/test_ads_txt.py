import tempfile
import unittest
from pathlib import Path

from app.ads.ads_txt import AdsSeller, generate_ads_txt, validate_ads_txt_content, write_ads_txt


class TestAdsTxt(unittest.TestCase):
    def test_generate_and_validate(self):
        content = generate_ads_txt(
            [
                AdsSeller("google.com", "pub-123", "DIRECT", "f08c47fec0942fa0"),
                AdsSeller("example-ssp.com", "acct-77", "RESELLER"),
            ]
        )
        report = validate_ads_txt_content(content, expected_domains=["google.com", "example-ssp.com"])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["records"]), 2)

    def test_invalid_line(self):
        report = validate_ads_txt_content("google.com,pub-1,INVALID", expected_domains=["google.com"])
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["errors"])

    def test_write_ads_txt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ads.txt"
            out = write_ads_txt("google.com, pub-1, DIRECT\n", str(path))
            self.assertTrue(Path(out).exists())


if __name__ == "__main__":
    unittest.main()
