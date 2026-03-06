import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from app.seo.feed_ops import generate_sitemap, generate_rss, monitor_indexing_status


class TestFeedOps(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "blogs.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                """
                CREATE TABLE blogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    content TEXT,
                    category TEXT,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO blogs(topic, content, category, status, created_at) VALUES(?,?,?,?,?)",
                ("Post A", "A content", "beauty", "published", "2026-01-01T00:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO blogs(topic, content, category, status, created_at) VALUES(?,?,?,?,?)",
                ("Post B", "B content", "living", "draft", "2026-01-02T00:00:00+00:00"),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def test_generate_sitemap_only_published(self):
        out = Path(self.tmp.name) / "sitemap.xml"
        report = generate_sitemap(site_url="https://example.com", output_path=str(out), db_path=str(self.db))
        self.assertEqual(report["count"], 1)

        tree = ET.parse(out)
        root = tree.getroot()
        locs = [n.text for n in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(len(locs), 1)
        self.assertIn("?p=1", locs[0])

    def test_generate_rss(self):
        out = Path(self.tmp.name) / "rss.xml"
        report = generate_rss(site_url="https://example.com", output_path=str(out), db_path=str(self.db))
        self.assertEqual(report["count"], 1)

        tree = ET.parse(out)
        root = tree.getroot()
        items = root.findall("channel/item")
        self.assertEqual(len(items), 1)

    def test_monitor_indexing_status(self):
        google = Path(self.tmp.name) / "google.json"
        naver = Path(self.tmp.name) / "naver.json"
        robots = Path(self.tmp.name) / "robots.txt"

        google.write_text(json.dumps({"errors": 0, "warnings": 1, "submitted": 10, "indexed": 9}), encoding="utf-8")
        naver.write_text(json.dumps({"errors": 0, "warnings": 0, "submitted": 8, "indexed": 7}), encoding="utf-8")
        robots.write_text("User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n", encoding="utf-8")

        report = monitor_indexing_status(str(google), str(naver), str(robots))
        self.assertIn(report["overall"], ["PASS", "WARN"])
        self.assertEqual(len(report["findings"]), 3)


if __name__ == "__main__":
    unittest.main()
