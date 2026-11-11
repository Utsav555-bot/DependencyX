import time
from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import (
    Project, Dependency, Package, Vulnerability, PackageVulnerability, ScanHistory, RiskAssessment, User
)
from backend.app.schemas.all_schemas import VulnerabilityItem, ScanHistoryResponse
from backend.app.core.security import get_current_user
from backend.app.core.logging import log_activity
from backend.app.vulnerability_engine.osv_client import osv_client
from backend.app.risk_engine.risk_calculator import RiskAnalysisEngine

router = APIRouter(prefix="", tags=["Vulnerability Detection Engine"])

@router.post("/projects/{project_id}/scan")
async def trigger_vulnerability_scan(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    deps = db.query(Dependency).filter(Dependency.project_id == project_id).all()
    if not deps:
        raise HTTPException(
            status_code=400,
            detail="No dependencies found for this project. Please upload a package-lock.json first."
        )

    start_time = time.time()
    
    # Create PENDING scan history
    scan_record = ScanHistory(
        project_id=project.id,
        scanned_by=current_user.id,
        status="IN_PROGRESS",
        total_packages=len(deps)
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    pkg_ids = list(set(d.package_id for d in deps))
    packages = db.query(Package).filter(Package.id.in_(pkg_ids)).all()
    pkg_by_id = {p.id: p for p in packages}

    vulnerable_packages_count = 0
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    all_found_vulns = []

    try:
        for dep in deps:
            pkg = pkg_by_id.get(dep.package_id)
            if not pkg:
                continue

            # Query OSV API (with caching)
            vuln_records = await osv_client.query_package(
                package_name=pkg.name,
                version=dep.resolved_version,
                ecosystem=pkg.ecosystem or "npm"
            )

            if vuln_records:
                vulnerable_packages_count += 1
                for v_data in vuln_records:
                    # Find or create Vulnerability record
                    vuln = db.query(Vulnerability).filter(Vulnerability.osv_id == v_data["osv_id"]).first()
                    if not vuln:
                        vuln = Vulnerability(
                            osv_id=v_data["osv_id"],
                            cve_id=v_data.get("cve_id"),
                            ghsa_id=v_data.get("ghsa_id"),
                            summary=v_data.get("summary"),
                            details=v_data.get("details"),
                            severity=v_data.get("severity", "MEDIUM"),
                            cvss_score=v_data.get("cvss_score"),
                            affected_ecosystem=v_data.get("affected_ecosystem", "npm"),
                            affected_package=v_data["affected_package"],
                            affected_range=v_data.get("affected_range"),
                            fixed_version=v_data.get("fixed_version"),
                            published_at=v_data.get("published_at")
                        )
                        db.add(vuln)
                        db.flush()

                    # Link package to vulnerability
                    pv = db.query(PackageVulnerability).filter(
                        PackageVulnerability.package_id == pkg.id,
                        PackageVulnerability.vulnerability_id == vuln.id,
                        PackageVulnerability.matched_version == dep.resolved_version
                    ).first()

                    if not pv:
                        pv = PackageVulnerability(
                            package_id=pkg.id,
                            vulnerability_id=vuln.id,
                            matched_version=dep.resolved_version
                        )
                        db.add(pv)

                    sev = v_data.get("severity", "MEDIUM")
                    if sev in sev_counts:
                        sev_counts[sev] += 1
                    all_found_vulns.append(v_data)

        duration_ms = int((time.time() - start_time) * 1000)

        # Update Scan History
        scan_record.status = "COMPLETED"
        scan_record.vulnerable_packages_count = vulnerable_packages_count
        scan_record.critical_count = sev_counts["CRITICAL"]
        scan_record.high_count = sev_counts["HIGH"]
        scan_record.medium_count = sev_counts["MEDIUM"]
        scan_record.low_count = sev_counts["LOW"]
        scan_record.duration_ms = duration_ms
        db.commit()

        # Compute updated Risk Assessment
        risk_result = RiskAnalysisEngine.calculate_project_risk(project_id, db)
        import json
        risk_assessment = RiskAssessment(
            project_id=project.id,
            scan_id=scan_record.id,
            overall_score=risk_result["overall_score"],
            risk_level=risk_result["risk_level"],
            max_depth=risk_result["max_depth"],
            critical_deps_count=risk_result["critical_deps_count"],
            spof_count=risk_result["spof_count"],
            direct_vulnerabilities=risk_result["direct_vulnerabilities"],
            transitive_vulnerabilities=risk_result["transitive_vulnerabilities"],
            details_json=json.dumps(risk_result["breakdown"])
        )
        db.add(risk_assessment)
        db.commit()

        log_activity(
            db,
            action="VULN_SCAN",
            entity_type="SCAN",
            entity_id=scan_record.id,
            user_id=current_user.id,
            organization_id=project.organization_id,
            details=f"Scan completed in {duration_ms}ms: {vulnerable_packages_count} vulnerable packages, {len(all_found_vulns)} CVEs/GHSAs"
        )

        return {
            "status": "COMPLETED",
            "scan_id": scan_record.id,
            "project_id": project.id,
            "total_packages_scanned": len(deps),
            "vulnerable_packages_count": vulnerable_packages_count,
            "critical_count": sev_counts["CRITICAL"],
            "high_count": sev_counts["HIGH"],
            "medium_count": sev_counts["MEDIUM"],
            "low_count": sev_counts["LOW"],
            "overall_risk_score": risk_result["overall_score"],
            "risk_level": risk_result["risk_level"],
            "duration_ms": duration_ms,
            "message": "Scan completed successfully." if vulnerable_packages_count > 0 else "No known vulnerability detected in this scan."
        }

    except Exception as e:
        db.rollback()
        scan_record.status = "FAILED"
        scan_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Vulnerability scan failed: {str(e)}")

@router.get("/projects/{project_id}/vulnerabilities", response_model=List[VulnerabilityItem])
def get_project_vulnerabilities(
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
    
    vulns = (
        db.query(Vulnerability)
        .join(PackageVulnerability, Vulnerability.id == PackageVulnerability.vulnerability_id)
        .filter(PackageVulnerability.package_id.in_(pkg_ids))
        .distinct()
        .all()
    )

    return [
        VulnerabilityItem(
            id=v.id,
            osv_id=v.osv_id,
            cve_id=v.cve_id,
            ghsa_id=v.ghsa_id,
            summary=v.summary,
            details=v.details,
            severity=v.severity,
            cvss_score=v.cvss_score,
            affected_package=v.affected_package,
            affected_range=v.affected_range,
            fixed_version=v.fixed_version,
            published_at=v.published_at
        )
        for v in vulns
    ]

@router.get("/vulnerabilities", response_model=List[VulnerabilityItem])
def list_all_vulnerabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vulns = db.query(Vulnerability).order_by(Vulnerability.retrieved_at.desc()).limit(100).all()
    return [
        VulnerabilityItem(
            id=v.id,
            osv_id=v.osv_id,
            cve_id=v.cve_id,
            ghsa_id=v.ghsa_id,
            summary=v.summary,
            details=v.details,
            severity=v.severity,
            cvss_score=v.cvss_score,
            affected_package=v.affected_package,
            affected_range=v.affected_range,
            fixed_version=v.fixed_version,
            published_at=v.published_at
        )
        for v in vulns
    ]
