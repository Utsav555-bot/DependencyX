import json
from typing import Dict, List, Any, Tuple, Optional
from backend.app.core.logging import logger

class PackageLockParseResult:
    def __init__(
        self,
        project_name: str,
        lockfile_version: int,
        packages: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]]
    ):
        self.project_name = project_name
        self.lockfile_version = lockfile_version
        self.packages = packages        # Distinct packages: [{"name": str, "version": str, ...}]
        self.dependencies = dependencies # Edges: [{"package_name": str, "resolved_version": str, "is_direct": bool, "depth": int, "parent_name": Optional[str], "type": str}]

class PackageLockParser:
    @staticmethod
    def parse(file_content: bytes) -> PackageLockParseResult:
        try:
            data = json.loads(file_content.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON format in package manifest: {str(e)}")

        if not isinstance(data, dict):
            raise ValueError("Invalid manifest structure: root element must be a JSON object.")

        lockfile_version = data.get("lockfileVersion", 1)
        project_name = data.get("name", "Unnamed Project")

        # In npm lockfiles v2 and v3, 'packages' dictionary is preferred
        if "packages" in data and isinstance(data["packages"], dict):
            return PackageLockParser._parse_v2_v3(data, lockfile_version, project_name)
        elif "dependencies" in data and isinstance(data["dependencies"], dict):
            return PackageLockParser._parse_v1(data, lockfile_version, project_name)
        else:
            raise ValueError(
                "Invalid npm manifest: missing 'packages' or 'dependencies' section. "
                "Ensure you uploaded a valid package-lock.json."
            )

    @staticmethod
    def _parse_v2_v3(data: Dict[str, Any], lockfile_version: int, project_name: str) -> PackageLockParseResult:
        raw_packages = data.get("packages", {})
        root_package = raw_packages.get("", {})
        
        # Direct dependencies declared in root
        direct_prod = set(root_package.get("dependencies", {}).keys())
        direct_dev = set(root_package.get("devDependencies", {}).keys())
        direct_peer = set(root_package.get("peerDependencies", {}).keys())
        all_direct = direct_prod | direct_dev | direct_peer

        packages_map: Dict[str, Dict[str, Any]] = {}
        dep_edges: List[Dict[str, Any]] = []

        # Map to find parent package based on node_modules path
        # Example path: "node_modules/axios/node_modules/follow-redirects"
        for path, info in raw_packages.items():
            if not path or path == "":
                continue

            parts = path.split("node_modules/")
            if len(parts) < 2:
                continue

            pkg_name = parts[-1].strip()
            # Clean scoped packages (e.g., @types/node)
            if pkg_name.endswith("/"):
                pkg_name = pkg_name[:-1]

            version = info.get("version", "unknown")
            is_direct = (len(parts) == 2 and pkg_name in all_direct)
            
            # Determine parent package
            parent_name = None
            if len(parts) > 2:
                parent_name = parts[-2].strip().rstrip("/")
            elif not is_direct and len(parts) == 2:
                # Transitive package installed at top level; find which direct package requires it
                # We will resolve this in second pass using requirements
                pass

            dep_type = "dependencies"
            if pkg_name in direct_dev or info.get("dev", False):
                dep_type = "devDependencies"
            elif pkg_name in direct_peer:
                dep_type = "peerDependencies"

            if pkg_name not in packages_map:
                packages_map[pkg_name] = {
                    "name": pkg_name,
                    "version": version,
                    "license": info.get("license"),
                    "description": None
                }

            dep_edges.append({
                "package_name": pkg_name,
                "resolved_version": version,
                "is_direct": is_direct,
                "depth": 1 if is_direct else 2,
                "parent_name": parent_name,
                "dependency_type": dep_type,
                "dependencies_declared": info.get("dependencies", {})
            })

        # Second pass to link child dependencies declared by parent
        # If parent_name is not set but pkg X declares pkg Y in its dependencies
        declared_child_to_parent: Dict[str, str] = {}
        for edge in dep_edges:
            parent = edge["package_name"]
            for child in edge.get("dependencies_declared", {}).keys():
                if child not in declared_child_to_parent:
                    declared_child_to_parent[child] = parent

        for edge in dep_edges:
            if not edge["is_direct"] and not edge["parent_name"]:
                edge["parent_name"] = declared_child_to_parent.get(edge["package_name"])
            edge.pop("dependencies_declared", None)

        return PackageLockParseResult(
            project_name=project_name,
            lockfile_version=lockfile_version,
            packages=list(packages_map.values()),
            dependencies=dep_edges
        )

    @staticmethod
    def _parse_v1(data: Dict[str, Any], lockfile_version: int, project_name: str) -> PackageLockParseResult:
        raw_deps = data.get("dependencies", {})
        packages_map: Dict[str, Dict[str, Any]] = {}
        dep_edges: List[Dict[str, Any]] = []

        def traverse_deps(deps_dict: Dict[str, Any], parent: Optional[str] = None, depth: int = 1):
            for name, details in deps_dict.items():
                version = details.get("version", "unknown")
                is_direct = (depth == 1)
                dep_type = "devDependencies" if details.get("dev", False) else "dependencies"

                if name not in packages_map:
                    packages_map[name] = {
                        "name": name,
                        "version": version,
                        "license": None,
                        "description": None
                    }

                dep_edges.append({
                    "package_name": name,
                    "resolved_version": version,
                    "is_direct": is_direct,
                    "depth": depth,
                    "parent_name": parent,
                    "dependency_type": dep_type
                })

                # Check nested dependencies
                nested = details.get("dependencies", {})
                if nested:
                    traverse_deps(nested, parent=name, depth=depth + 1)

        traverse_deps(raw_deps, parent=None, depth=1)

        return PackageLockParseResult(
            project_name=project_name,
            lockfile_version=lockfile_version,
            packages=list(packages_map.values()),
            dependencies=dep_edges
        )
