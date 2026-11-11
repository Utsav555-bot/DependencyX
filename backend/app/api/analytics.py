from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.session import get_db
from backend.app.models.entities import (
    Project, Dependency, Package, Vulnerability, PackageVulnerability, ScanHistory, RiskAssessment, ActivityLog, OrganizationMember, User
)
from backend.app.schemas.all_schemas import DashboardAnalyticsResponse, DashboardMetrics, SeverityDistribution, DepthDistribution
from backend.app.core.security import get_current_user
from backend.app.risk_engine.risk_calculator import RiskAnalysisEngine

router = APIRouter(prefix="/analytics", tags=["Security Dashboard & Analytics"])

@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    org_id = membership.organization_id if membership else None

    # 1. Projects in user's organization
    projects = db.query(Project).filter(Project.organization_id == org_id).all()
    project_ids = [p.id for p in projects]
    total_projects = len(projects)

    # 2. Dependencies & Unique Packages
    dependencies_query = db.query(Dependency).filter(Dependency.project_id.in_(project_ids))
    total_dependencies = dependencies_query.count()
    total_unique_packages = dependencies_query.with_entities(Dependency.package_id).distinct().count()

    # 3. Vulnerability counts
    package_ids_query = dependencies_query.with_entities(Dependency.package_id).distinct()
    pkg_vulns = (
        db.query(PackageVulnerability, Vulnerability)
        .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
        .filter(PackageVulnerability.package_id.in_(package_ids_query))
        .all()
    )

    vulnerable_packages_set = set(pv.package_id for pv, v in pkg_vulns)
    vulnerable_packages_count = len(vulnerable_packages_set)

    critical_vulns_count = sum(1 for pv, v in pkg_vulns if v.severity == "CRITICAL")
    high_vulns_count = sum(1 for pv, v in pkg_vulns if v.severity == "HIGH")
    medium_vulns_count = sum(1 for pv, v in pkg_vulns if v.severity == "MEDIUM")
    low_vulns_count = sum(1 for pv, v in pkg_vulns if v.severity == "LOW")

    # 4. Project risk comparisons & overall organization risk
    project_risk_comparison = []
    high_risk_projects_count = 0
    total_risk_accum = 0.0
    affected_projects_set = set()

    for p in projects:
        r = RiskAnalysisEngine.calculate_project_risk(p.id, db)
        score = r["overall_score"]
        level = r["risk_level"]
        total_risk_accum += score

        if level in ["HIGH", "CRITICAL"]:
            high_risk_projects_count += 1
        if r["vulnerable_packages"]:
            affected_projects_set.add(p.id)

        project_risk_comparison.append({
            "project_id": p.id,
            "project_name": p.name,
            "risk_score": score,
            "risk_level": level,
            "vulnerabilities": len(r["vulnerable_packages"]),
            "spof_count": r["spof_count"]
        })

    overall_org_risk = round(total_risk_accum / total_projects, 1) if total_projects > 0 else 0.0

    # 5. Severity distribution
    severity_distribution = [
        SeverityDistribution(severity="CRITICAL", count=critical_vulns_count),
        SeverityDistribution(severity="HIGH", count=high_vulns_count),
        SeverityDistribution(severity="MEDIUM", count=medium_vulns_count),
        SeverityDistribution(severity="LOW", count=low_vulns_count),
    ]

    # 6. Depth distribution
    depth_counts: Dict[int, int] = {}
    depth_rows = (
        db.query(Dependency.depth, func.count(Dependency.id))
        .filter(Dependency.project_id.in_(project_ids))
        .group_by(Dependency.depth)
        .all()
    )
    for d, cnt in depth_rows:
        depth_counts[d] = cnt

    depth_distribution = [
        DepthDistribution(depth=d, count=depth_counts.get(d, 0))
        for d in sorted(depth_counts.keys())
    ] if depth_counts else [DepthDistribution(depth=1, count=0)]

    # 7. Top vulnerable packages
    vuln_pkg_counts: Dict[str, Dict[str, Any]] = {}
    pkg_id_name_map = {
        p.id: p.name for p in db.query(Package).filter(Package.id.in_(vulnerable_packages_set)).all()
    }

    for pv, v in pkg_vulns:
        pkg_name = pkg_id_name_map.get(pv.package_id, "unknown")
        if pkg_name not in vuln_pkg_counts:
            vuln_pkg_counts[pkg_name] = {
                "package_name": pkg_name,
                "vulnerabilities_count": 0,
                "highest_severity": v.severity,
                "cve_ids": []
            }
        vuln_pkg_counts[pkg_name]["vulnerabilities_count"] += 1
        if v.cve_id:
            vuln_pkg_counts[pkg_name]["cve_ids"].append(v.cve_id)

    top_vulnerable_packages = sorted(
        vuln_pkg_counts.values(),
        key=lambda x: x["vulnerabilities_count"],
        reverse=True
    )[:5]

    # 8. Recent activity
    recent_activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.organization_id == org_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(8)
        .all()
    )
    recent_activity_data = [
        {
            "id": a.id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": a.created_at.isoformat()
        }
        for a in recent_activities
    ]

    # 9. Latest vulnerability alerts
    latest_alerts_raw = (
        db.query(Vulnerability)
        .order_by(Vulnerability.retrieved_at.desc())
        .limit(5)
        .all()
    )
    latest_alerts = [
        {
            "id": v.id,
            "osv_id": v.osv_id,
            "cve_id": v.cve_id,
            "package_name": v.affected_package,
            "severity": v.severity,
            "summary": v.summary,
            "fixed_version": v.fixed_version
        }
        for v in latest_alerts_raw
    ]

    return DashboardAnalyticsResponse(
        metrics=DashboardMetrics(
            total_projects=total_projects,
            total_unique_packages=total_unique_packages,
            total_dependencies=total_dependencies,
            vulnerable_packages=vulnerable_packages_count,
            critical_vulnerabilities=critical_vulns_count,
            high_risk_projects=high_risk_projects_count,
            affected_projects=len(affected_projects_set),
            overall_org_risk_score=overall_org_risk
        ),
        severity_distribution=severity_distribution,
        top_vulnerable_packages=top_vulnerable_packages,
        project_risk_comparison=project_risk_comparison,
        depth_distribution=depth_distribution,
        recent_activity=recent_activity_data,
        latest_alerts=latest_alerts
    )
