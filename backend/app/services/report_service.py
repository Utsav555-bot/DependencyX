import csv
import io
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.entities import Project, Dependency, Package, Vulnerability, PackageVulnerability, ScanHistory, RiskAssessment

class ReportService:
    @staticmethod
    def generate_csv_report(project_id: str, db: Session) -> str:
        """
        Generates CSV security audit report for project dependencies and vulnerabilities.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")

        output = io.StringIO()
        writer = csv.writer(output)

        # Header info
        writer.writerow(["DependencyX Security Audit Report"])
        writer.writerow(["Project Name", project.name])
        writer.writerow(["Project ID", project.id])
        writer.writerow(["Ecosystem", project.ecosystem])
        writer.writerow(["Report Date (UTC)", datetime.now(timezone.utc).isoformat()])
        writer.writerow([])

        # Table header
        writer.writerow([
            "Package Name",
            "Resolved Version",
            "Dependency Type",
            "Depth",
            "Is Direct",
            "Is Vulnerable",
            "Highest Severity",
            "OSV ID",
            "CVE ID",
            "CVSS Score",
            "Summary",
            "Fixed Version"
        ])

        # Fetch dependencies
        deps = db.query(Dependency).filter(Dependency.project_id == project_id).all()
        pkg_ids = [d.package_id for d in deps]
        pkgs = {p.id: p.name for p in db.query(Package).filter(Package.id.in_(pkg_ids)).all()}

        pkg_vulns = (
            db.query(PackageVulnerability, Vulnerability)
            .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
            .filter(PackageVulnerability.package_id.in_(pkg_ids))
            .all()
        )
        vuln_map: Dict[str, List[Vulnerability]] = {}
        for pv, v in pkg_vulns:
            vuln_map.setdefault(pv.package_id, []).append(v)

        for dep in deps:
            pkg_name = pkgs.get(dep.package_id, "unknown")
            vulns = vuln_map.get(dep.package_id, [])

            if vulns:
                for v in vulns:
                    writer.writerow([
                        pkg_name,
                        dep.resolved_version,
                        dep.dependency_type,
                        dep.depth,
                        "Yes" if dep.is_direct else "No",
                        "YES",
                        v.severity,
                        v.osv_id,
                        v.cve_id or "N/A",
                        v.cvss_score or "N/A",
                        v.summary or "N/A",
                        v.fixed_version or "None"
                    ])
            else:
                writer.writerow([
                    pkg_name,
                    dep.resolved_version,
                    dep.dependency_type,
                    dep.depth,
                    "Yes" if dep.is_direct else "No",
                    "NO",
                    "NONE",
                    "N/A",
                    "N/A",
                    "N/A",
                    "No known vulnerabilities",
                    "N/A"
                ])

        return output.getvalue()

    @staticmethod
    def generate_html_report(project_id: str, db: Session) -> str:
        """
        Generates comprehensive HTML executive security report.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")

        risk = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.project_id == project_id)
            .order_by(RiskAssessment.created_at.desc())
            .first()
        )
        scan = (
            db.query(ScanHistory)
            .filter(ScanHistory.project_id == project_id)
            .order_by(ScanHistory.created_at.desc())
            .first()
        )

        overall_score = risk.overall_score if risk else 0.0
        risk_level = risk.risk_level if risk else "LOW"
        max_depth = risk.max_depth if risk else 1
        spof_count = risk.spof_count if risk else 0

        color_map = {
            "CRITICAL": "#DC2626",
            "HIGH": "#EA580C",
            "MEDIUM": "#D97706",
            "LOW": "#16A34A"
        }
        badge_color = color_map.get(risk_level, "#16A34A")

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DependencyX Security Report - {project.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0F172A; color: #F1F5F9; padding: 40px; margin: 0; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #1E293B; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
        .header {{ border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 24px; }}
        .title {{ font-size: 26px; font-weight: 700; color: #38BDF8; margin: 0; }}
        .subtitle {{ font-size: 14px; color: #94A3B8; margin-top: 6px; }}
        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; color: white; background: {badge_color}; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
        .metric-card {{ background: #0F172A; padding: 18px; border-radius: 8px; border: 1px solid #334155; text-align: center; }}
        .metric-val {{ font-size: 24px; font-weight: bold; color: #38BDF8; margin-top: 4px; }}
        .metric-label {{ font-size: 12px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #64748B; border-top: 1px solid #334155; padding-top: 16px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">DependencyX — Software Dependency Risk Map</h1>
            <p class="subtitle">Executive Security Audit & Risk Evaluation Report</p>
            <div style="margin-top: 12px;">
                <span class="badge">Risk Level: {risk_level} ({overall_score}/100)</span>
            </div>
        </div>
        <p><strong>Target Project:</strong> {project.name} ({project.ecosystem})</p>
        <p><strong>Generated At:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Overall Risk Score</div>
                <div class="metric-val">{overall_score}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Graph Depth</div>
                <div class="metric-val">{max_depth}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Single Points of Failure</div>
                <div class="metric-val">{spof_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Vulnerable Packages</div>
                <div class="metric-val">{scan.vulnerable_packages_count if scan else 0}</div>
            </div>
        </div>

        <h3>Risk Engine Methodology</h3>
        <p style="color: #94A3B8; line-height: 1.6; font-size: 14px;">
            DependencyX analyzes direct and transitive dependency trees using NetworkX directed graph analysis. 
            Risk calculations synthesize peak vulnerability severity, CVSS metrics, graph depth attenuation, 
            betweenness centrality, and cross-project blast radius within your organization.
        </p>

        <div class="footer">
            Generated automatically by DependencyX &bull; Cloud Security & RDBMS DP-900 Project
        </div>
    </div>
</body>
</html>"""
