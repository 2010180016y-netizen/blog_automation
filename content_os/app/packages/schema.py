from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PackageMetadata(BaseModel):
    name: str
    version: str
    description: Optional[str] = ""
    category: str
    includes: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)

class PackageManifest(BaseModel):
    metadata: PackageMetadata
    content_map: Dict[str, str] # Map of resource type to file path
