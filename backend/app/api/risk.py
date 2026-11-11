from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Project, OrganizationMember, Dependency, Package, Vulnerability, PackageVulnerability, User
from backend.app.schemas.all_schemas import RiskDetailsResponse
from backend.app.core.security import get_current_user
from backend.app.risk_engine.risk_calculator import RiskAnalysisEngine

router = APIRouter(prefix="", tags=["Risk Analysis Engine"])

@router.get("/projects/{project_id}/risk", response_model=RiskDetailsResponse)
def get_project_risk_assessment(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    risk_data = RiskAnalysisEngine.calculate_project_risk(project_id, db)

    return RiskDetailsResponse(
        project_id=project.id,
        project_name=project.name,
        overall_score=risk_data["overall_score"],
        risk_level=risk_data["risk_level"],
        max_depth=risk_data["max_depth"],
        critical_deps_count=risk_data["critical_deps_count"],
        spof_count=risk_data["spof_count"],
        direct_vulnerabilities=risk_data["direct_vulnerabilities"],
        transitive_vulnerabilities=risk_data["transitive_vulnerabilities"],
        vulnerable_packages=risk_data["vulnerable_packages"],
        critical_dependencies=risk_data["critical_dependencies"],
        single_points_of_failure=risk_data["single_points_of_failure"],
        breakdown=risk_data["breakdown"]
    )

@router.get("/risk/organization")
def get_organization_risk(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    org_id = membership.organization_id if membership else None

    projects = db.query(Project).filter(Project.organization_id == org_id).all()
    if not projects:
        return {"overall_org_risk": 0.0, "total_projects": 0, "projects_risk": []}

    total_score = 0.0
    projects_risk = []
    for p in projects:
        r = RiskAnalysisEngine.calculate_project_risk(p.id, db)
        total_score += r["overall_score"]
        projects_risk.append({
            "project_id": p.id,
            "project_name": p.name,
            "risk_score": r["overall_score"],
            "risk_level": r["risk_level"],
            "spof_count": r["spof_count"],
            "vulnerable_count": len(r["vulnerable_packages"])
        })

    avg_score = round(total_score / len(projects), 1)

    return {
        "overall_org_risk": avg_score,
        "total_projects": len(projects),
        "projects_risk": projects_risk
    }

@router.get("/risk/critical-dependencies")
def get_critical_dependencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    org_id = membership.organization_id if membership else None

    # Fetch all project dependencies in organization
    org_projects = db.query(Project.id).filter(Project.organization_id == org_id).all()
    org_proj_ids = [p[0] for p in org_projects]

    all_deps = db.query(Dependency).filter(Dependency.project_id.in_(org_proj_ids)).all()
    pkg_ids = list(set(d.package_id for d in all_deps))
    packages = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(pkg_ids)).all()}

    # Map package to set of distinct projects using it
    pkg_projects: Dict[str, set] = {}
    for d in all_deps:
        pkg_projects.setdefault(d.package_id, set()).add(d.project_id)

    # Vulnerability status
    pkg_vulns = (
        db.query(PackageVulnerability, Vulnerability)
        .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
        .filter(PackageVulnerability.package_id.in_(pkg_ids))
        .all()
    )
    vuln_map: Dict[str, List[Vulnerability]] = {}
    for pv, v in pkg_vulns:
        vuln_map.setdefault(pv.package_id, []).append(v)

    critical_list = []
    for pkg_id, prj_set in pkg_projects.items():
        pkg_name = packages.get(pkg_id, "unknown")
        project_count = len(prj_set)
        vulns = vuln_map.get(pkg_id, [])

        highest_sev = "NONE"
        if vulns:
            sevs = [v.severity for v in vulns]
            if "CRITICAL" in sevs:
                highest_sev = "CRITICAL"
            elif "HIGH" in sevs:
                highest_sev = "HIGH"
            elif "MEDIUM" in sevs:
                highest_sev = "MEDIUM"
            else:
                highest_sev = "LOW"

        # Classification
        if project_count >= 2 or len(vulns) > 0:
            is_spof = project_count >= 2 and len(vulns) > 0
            critical_list.append({
                "package_id": pkg_id,
                "package_name": pkg_name,
                "affected_projects_count": project_count,
                "has_vulnerability": len(vulns) > 0,
                "highest_severity": highest_sev,
                "is_single_point_of_failure": is_spof,
                "reason": (
                    f"Shared by {project_count} projects; contains active {highest_sev} vulnerability"
                    if is_spof else
                    f"Shared across {project_count} separate application codebases"
                    if project_count >= 2 else
                    f"Direct target with {highest_sev} vulnerability"
                )
            })

    # Sort by project count and severity
    critical_list.sort(key=lambda x: (x["is_single_point_of_failure"], x["affected_projects_count"]), reverse=True)
    return critical_list
