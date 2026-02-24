import httpx
import logging
from typing import Dict, Optional

class WordPressPublisher:
    def __init__(self, api_base: str, username: str, password: str):
        self.api_base = api_base.rstrip('/')
        self.auth = (username, password)

    async def publish(self, title: str, content: str, status: str = "draft", categories: list = None, tags: list = None) -> Dict:
        url = f"{self.api_base}/posts"
        payload = {
            "title": title,
            "content": content,
            "status": status,
            "categories": categories or [],
            "tags": tags or []
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, auth=self.auth, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logging.error(f"WP API Error: {e.response.text}")
                raise
            except Exception as e:
                logging.error(f"WP Connection Error: {e}")
                raise
