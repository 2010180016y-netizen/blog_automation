from typing import Dict, List, Optional
from .schema import PackageMetadata, PackageManifest

class PackageRegistry:
    def __init__(self):
        self.packages: Dict[str, Dict[str, PackageManifest]] = {} # name -> version -> manifest

    def register(self, manifest: PackageManifest):
        name = manifest.metadata.name
        version = manifest.metadata.version
        
        if name not in self.packages:
            self.packages[name] = {}
        
        self.packages[name][version] = manifest

    def get_package(self, name: str, version: Optional[str] = None) -> Optional[PackageManifest]:
        if name not in self.packages:
            return None
        
        if version:
            return self.packages[name].get(version)
        
        # Return latest version (naive semver sort)
        versions = sorted(self.packages[name].keys(), reverse=True)
        return self.packages[name][versions[0]] if versions else None

    def list_packages(self) -> List[PackageMetadata]:
        results = []
        for name in self.packages:
            for version in self.packages[name]:
                results.append(self.packages[name][version].metadata)
        return results
