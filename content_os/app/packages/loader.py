import os
import json
from typing import Optional
from .schema import PackageManifest, PackageMetadata
from .registry import PackageRegistry

class PackageLoader:
    def __init__(self, base_path: str, registry: PackageRegistry):
        self.base_path = base_path
        self.registry = registry

    def scan_and_load(self):
        """
        Scans the base_path for package directories and loads manifests.
        Expected structure: base_path/package_name/v1.0.0/manifest.json
        """
        if not os.path.exists(self.base_path):
            return

        for pkg_name in os.listdir(self.base_path):
            pkg_path = os.path.join(self.base_path, pkg_name)
            if not os.path.isdir(pkg_path):
                continue
            
            for version in os.listdir(pkg_path):
                version_path = os.path.join(pkg_path, version)
                manifest_file = os.path.join(version_path, "manifest.json")
                
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        manifest = PackageManifest(**data)
                        self.registry.register(manifest)

    def load_resource(self, manifest: PackageManifest, resource_type: str) -> Optional[str]:
        """
        Loads the actual content of a resource (e.g., a template file).
        """
        relative_path = manifest.content_map.get(resource_type)
        if not relative_path:
            return None
            
        # Path is relative to the package version directory
        full_path = os.path.join(
            self.base_path, 
            manifest.metadata.name, 
            manifest.metadata.version, 
            relative_path
        )
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
