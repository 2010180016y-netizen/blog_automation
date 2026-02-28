from pydantic import BaseModel
from typing import List, Optional, Dict

class ComplianceRequest(BaseModel):
    content: str
    language: str = "ko"
    category: str = "General"
    is_sponsored: bool = False
    disclosure_required: bool = False

class ComplianceResult(BaseModel):
    status: str  # PASS, WARN, REJECT
    fail: List[Dict[str, str]] = []
    warn: List[Dict[str, str]] = []
    suggestions: List[str] = []
