from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ContentEntry(BaseModel):
    id: Optional[int] = None
    content: str
    paragraphs: List[str]
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
