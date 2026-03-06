from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET


@dataclass
class FeedItem:
    id: int
    title: str
    content: str
    category: Optional[str]
    created_at: str


def _load_published_items(db_path: str = "blogs.db", limit: int = 500, category: Optional[str] = None) -> List[FeedItem]:
    query = "SELECT id, topic, content, category, created_at FROM blogs WHERE status = 'published'"
    params: List[object] = []
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows: List[FeedItem] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(query, params):
            rows.append(
                FeedItem(
                    id=int(row["id"]),
                    title=row["topic"] or "Untitled",
                    content=row["content"] or "",
                    category=row["category"],
                    created_at=row["created_at"] or datetime.now(timezone.utc).isoformat(),
                )
            )
    return rows


def generate_sitemap(
    site_url: str,
    output_path: str,
    db_path: str = "blogs.db",
    category: Optional[str] = None,
    changefreq: str = "daily",
    priority: str = "0.7",
) -> Dict:
    items = _load_published_items(db_path=db_path, category=category)

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for item in items:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{site_url.rstrip('/')}/?p={item.id}"
        lastmod = ET.SubElement(url, "lastmod")
        lastmod.text = item.created_at
        cf = ET.SubElement(url, "changefreq")
        cf.text = changefreq
        pr = ET.SubElement(url, "priority")
        pr.text = priority

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(urlset).write(path, encoding="utf-8", xml_declaration=True)

    return {
        "type": "sitemap",
        "path": str(path),
        "count": len(items),
        "category": category,
    }


def _to_rfc2822(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def generate_rss(
    site_url: str,
    output_path: str,
    db_path: str = "blogs.db",
    category: Optional[str] = None,
    channel_title: str = "Content OS Feed",
    channel_description: str = "Latest published content",
) -> Dict:
    items = _load_published_items(db_path=db_path, category=category)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = channel_title
    ET.SubElement(channel, "link").text = site_url.rstrip("/")
    ET.SubElement(channel, "description").text = channel_description

    for item in items:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item.title
        ET.SubElement(node, "link").text = f"{site_url.rstrip('/')}/?p={item.id}"
        ET.SubElement(node, "guid").text = f"{site_url.rstrip('/')}/?p={item.id}"
        ET.SubElement(node, "pubDate").text = _to_rfc2822(item.created_at)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(rss).write(path, encoding="utf-8", xml_declaration=True)

    return {
        "type": "rss",
        "path": str(path),
        "count": len(items),
        "category": category,
    }


def monitor_indexing_status(
    google_status_json: Optional[str] = None,
    naver_status_json: Optional[str] = None,
    robots_txt: Optional[str] = None,
) -> Dict:
    findings: List[Dict] = []

    def _load(path: Optional[str], source: str):
        if not path:
            findings.append({"source": source, "status": "UNVERIFIED", "detail": "status file not provided"})
            return None
        p = Path(path)
        if not p.exists():
            findings.append({"source": source, "status": "UNVERIFIED", "detail": f"missing file: {path}"})
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    google = _load(google_status_json, "google_search_console")
    naver = _load(naver_status_json, "naver_search_advisor")

    for source, data in (("google_search_console", google), ("naver_search_advisor", naver)):
        if not data:
            continue
        errors = int(data.get("errors", 0))
        warnings = int(data.get("warnings", 0))
        submitted = int(data.get("submitted", 0))
        indexed = int(data.get("indexed", 0))
        status = "PASS" if errors == 0 else "FAIL"
        findings.append(
            {
                "source": source,
                "status": status,
                "errors": errors,
                "warnings": warnings,
                "submitted": submitted,
                "indexed": indexed,
            }
        )

    if robots_txt:
        robots_path = Path(robots_txt)
        if robots_path.exists():
            content = robots_path.read_text(encoding="utf-8")
            has_sitemap = "Sitemap:" in content
            allows_naver = "User-agent: Yeti" in content or "User-agent: *" in content
            findings.append(
                {
                    "source": "robots_txt",
                    "status": "PASS" if has_sitemap else "WARN",
                    "has_sitemap_directive": has_sitemap,
                    "naver_agent_present": allows_naver,
                }
            )
        else:
            findings.append({"source": "robots_txt", "status": "UNVERIFIED", "detail": f"missing file: {robots_txt}"})

    overall = "PASS"
    if any(f.get("status") == "FAIL" for f in findings):
        overall = "FAIL"
    elif any(f.get("status") in ("WARN", "UNVERIFIED") for f in findings):
        overall = "WARN"

    return {
        "overall": overall,
        "findings": findings,
    }


def send_ops_alert(report: Dict, webhook_url: Optional[str] = None, email_to: Optional[str] = None) -> Dict:
    # lightweight stub for integrations
    emitted = {
        "webhook": bool(webhook_url),
        "email": bool(email_to),
        "overall": report.get("overall"),
    }

    if webhook_url:
        try:
            import httpx

            with httpx.Client(timeout=10.0) as client:
                client.post(webhook_url, json=report)
        except Exception:
            emitted["webhook"] = False

    if email_to:
        # keep as operation stub for SMTP integration in deployment env
        emitted["email_stub_message"] = f"Configure SMTP relay to send report to {email_to}"

    return emitted
