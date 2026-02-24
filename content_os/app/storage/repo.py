import sqlite3
import json
from typing import List, Optional
from .models import ContentEntry

class ContentRepo:
    def __init__(self, db_path: str = "blogs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    paragraphs TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_content(self, entry: ContentEntry):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO contents (content, paragraphs, metadata) VALUES (?, ?, ?)",
                (entry.content, json.dumps(entry.paragraphs), json.dumps(entry.metadata))
            )
            return cursor.lastrowid

    def get_all_paragraphs(self) -> List[str]:
        all_paras = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT paragraphs FROM contents")
            for row in cursor:
                all_paras.extend(json.loads(row[0]))
        return all_paras

    def get_all_entries(self) -> List[ContentEntry]:
        entries = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, content, paragraphs, metadata, created_at FROM contents")
            for row in cursor:
                entries.append(ContentEntry(
                    id=row[0],
                    content=row[1],
                    paragraphs=json.loads(row[2]),
                    metadata=json.loads(row[3]),
                    created_at=row[4]
                ))
        return entries
