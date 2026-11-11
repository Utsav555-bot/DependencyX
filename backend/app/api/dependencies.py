from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Project, Dependency, Package, Vulnerability, PackageVulnerability, User
from backend.app.schemas.all_schemas import DependencyItem, GraphResponse
from backend.app.core.security import get_current_user
from backend.app.core.logging import log_activity
from backend.app.services.parser import PackageLockParser
from backend.app.storage.blob_storage import storage_service
from backend.app.graph_engine.graph_service import DependencyGraphService

router = APIRouter(prefix="/projects", tags=["Dependencies & Graph Engine"])

@router.post("/{project_id}/upload")
async def upload_package_manifest(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Upload a valid package-lock.json file."
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Manifest file size exceeds 10MB limit.")

    # Parse manifest
    try:
        parsed = PackageLockParser.parse(content)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse manifest: {str(e)}")

    # Store file in Azure Blob Storage / local disk
    storage_path = f"manifests/{project_id}/package-lock.json"
    saved_blob_uri = await storage_service.upload_file(content, storage_path, content_type="application/json")
    project.manifest_blob_path = saved_blob_uri

    # Atomic database transaction: Upsert packages and replace project dependencies
    try:
        # Delete existing dependencies for clean re-import
        db.query(Dependency).filter(Dependency.project_id == project_id).delete()

        # Step 1: Ingest or lookup packages in master Packages table
        packages_dict = {}
        for pkg_data in parsed.packages:
            name = pkg_data["name"]
            pkg = db.query(Package).filter(
                Package.name == name,
                Package.ecosystem == project.ecosystem
            ).first()

            if not pkg:
                pkg = Package(
                    name=name,
                    ecosystem=project.ecosystem,
                    latest_version=pkg_data["version"],
                    license=pkg_data.get("license")
                )
                db.add(pkg)
                db.flush()
            packages_dict[name] = pkg

        # Step 2: Ingest dependency relationships
        for dep_data in parsed.dependencies:
            pkg_name = dep_data["package_name"]
            pkg = packages_dict.get(pkg_name)
            if not pkg:
                continue

            parent_pkg = packages_dict.get(dep_data.get("parent_name")) if dep_data.get("parent_name") else None

            dep = Dependency(
                project_id=project.id,
                package_id=pkg.id,
                resolved_version=dep_data["resolved_version"],
                is_direct=dep_data["is_direct"],
                dependency_type=dep_data.get("dependency_type", "dependencies"),
                depth=dep_data.get("depth", 1 if dep_data["is_direct"] else 2),
                parent_package_id=parent_pkg.id if parent_pkg else None
            )
            db.add(dep)

        db.commit()

        log_activity(
            db,
            action="MANIFEST_UPLOAD",
            entity_type="PROJECT",
            entity_id=project.id,
            user_id=current_user.id,
            organization_id=project.organization_id,
            details=f"Uploaded manifest: {len(parsed.packages)} packages, {len(parsed.dependencies)} dependencies (lockfile v{parsed.lockfile_version})"
        )

        return {
            "message": "Manifest parsed and stored successfully.",
            "project_id": project.id,
            "project_name": parsed.project_name,
            "lockfile_version": parsed.lockfile_version,
            "total_packages": len(parsed.packages),
            "total_dependencies": len(parsed.dependencies),
            "storage_path": saved_blob_uri
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database transaction failed during manifest ingestion: {str(e)}"
        )

@router.get("/{project_id}/dependencies", response_model=List[DependencyItem])
def get_project_dependencies(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    deps = db.query(Dependency).filter(Dependency.project_id == project_id).all()
    if not deps:
        return []

    pkg_ids = [d.package_id for d in deps]
    pkgs = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(pkg_ids)).all()}

    # Parent package names
    parent_ids = [d.parent_package_id for d in deps if d.parent_package_id]
    parents = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(parent_ids)).all()}

    # Matched vulnerabilities
    pkg_vulns = (
        db.query(PackageVulnerability, Vulnerability)
        .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
        .filter(PackageVulnerability.package_id.in_(pkg_ids))
        .all()
    )
    vuln_map: Dict[str, List[Vulnerability]] = {}
    for pv, v in pkg_vulns:
        vuln_map.setdefault(pv.package_id, []).append(v)

    results = []
    for d in deps:
        vulns = vuln_map.get(d.package_id, [])
        highest_sev = "NONE"
        if vulns:
            severities = [v.severity for v in vulns]
            if "CRITICAL" in severities:
                highest_sev = "CRITICAL"
            elif "HIGH" in severities:
                highest_sev = "HIGH"
            elif "MEDIUM" in severities:
                highest_sev = "MEDIUM"
            else:
                highest_sev = "LOW"

        results.append(DependencyItem(
            id=d.id,
            package_name=pkgs.get(d.package_id, "unknown"),
            resolved_version=d.resolved_version,
            is_direct=d.is_direct,
            dependency_type=d.dependency_type,
            depth=d.depth,
            parent_package_name=parents.get(d.parent_package_id),
            has_vulnerability=len(vulns) > 0,
            highest_severity=highest_sev
        ))

    return results

@router.get("/{project_id}/graph", response_model=GraphResponse)
def get_dependency_graph(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    deps = db.query(Dependency).filter(Dependency.project_id == project_id).all()
    if not deps:
        return GraphResponse(
            root_node_id=f"root_{project_id}",
            nodes=[{
                "id": f"root_{project_id}",
                "type": "customDependency",
                "position": {"x": 0, "y": 0},
                "data": {
                    "id": f"root_{project_id}",
                    "label": project.name,
                    "version": "1.0.0",
                    "node_type": "project_root",
                    "is_direct": True,
                    "depth": 0,
                    "is_vulnerable": False,
                    "highest_severity": "NONE",
                    "vulnerabilities": []
                }
            }],
            edges=[],
            summary={"total_nodes": 1, "total_edges": 0, "max_depth": 0, "has_circular": False}
        )

    pkg_ids = [d.package_id for d in deps]
    pkgs = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(pkg_ids)).all()}
    parent_ids = [d.parent_package_id for d in deps if d.parent_package_id]
    parents = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(parent_ids)).all()}

    # Matched vulnerabilities
    pkg_vulns = (
        db.query(PackageVulnerability, Vulnerability)
        .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
        .filter(PackageVulnerability.package_id.in_(pkg_ids))
        .all()
    )
    vuln_map: Dict[str, List[Dict[str, Any]]] = {}
    for pv, v in pkg_vulns:
        pkg_name = pkgs.get(pv.package_id, "unknown")
        vuln_map.setdefault(pkg_name, []).append({
            "osv_id": v.osv_id,
            "cve_id": v.cve_id,
            "severity": v.severity,
            "cvss_score": v.cvss_score,
            "summary": v.summary,
            "fixed_version": v.fixed_version
        })

    # Prepare dependencies payload for NetworkX graph builder
    deps_payload = []
    for d in deps:
        deps_payload.append({
            "package_id": d.package_id,
            "package_name": pkgs.get(d.package_id, "unknown"),
            "resolved_version": d.resolved_version,
            "is_direct": d.is_direct,
            "parent_name": parents.get(d.parent_package_id),
            "parent_package_id": d.parent_package_id,
            "depth": d.depth
        })

    graph_data = DependencyGraphService.build_project_graph(
        project_id=project.id,
        project_name=project.name,
        dependencies=deps_payload,
        package_vulns_map=vuln_map
    )

    return graph_data
