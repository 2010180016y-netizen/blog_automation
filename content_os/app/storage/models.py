from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ContentEntry(BaseModel):
    id: Optional[int] = None
    content: str
    paragraphs: List[str]
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class ProductSSOTEntry(BaseModel):
    sku: str
    source_type: str = "MY_STORE"
    name: Optional[str] = None
    price: Optional[int] = None
    shipping: Optional[str] = None
    product_link: Optional[str] = None
    options: str = "{}"
    as_info: str = ""
    mandatory_disclaimer: str = ""
    evidence_data: Optional[Dict] = None
