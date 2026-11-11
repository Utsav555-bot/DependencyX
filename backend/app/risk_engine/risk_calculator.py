import networkx as nx
from typing import Dict, List, Any, Set, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import Project, Dependency, Package, Vulnerability, PackageVulnerability
from backend.app.config import settings
from backend.app.core.logging import logger

class RiskAnalysisEngine:
    @staticmethod
    def calculate_project_risk(
        project_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Executes comprehensive risk calculations for a project:
        - NetworkX graph depth calculations
        - Reverse vulnerability propagation traversal
        - Cross-project impact assessment
        - Critical dependencies and Single Points of Failure (SPOF)
        - Transparent 0-100 composite risk score with explainability
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")

        # 1. Fetch all dependencies for this project
        deps = db.query(Dependency).filter(Dependency.project_id == project_id).all()
        if not deps:
            return {
                "overall_score": 0.0,
                "risk_level": "LOW",
                "max_depth": 0,
                "critical_deps_count": 0,
                "spof_count": 0,
                "direct_vulnerabilities": 0,
                "transitive_vulnerabilities": 0,
                "vulnerable_packages": [],
                "propagation_paths": [],
                "critical_dependencies": [],
                "single_points_of_failure": [],
                "breakdown": {
                    "vulnerability_component": 0.0,
                    "depth_component": 0.0,
                    "blast_radius_component": 0.0,
                    "centrality_component": 0.0
                }
            }

        # 2. Build Project Graph in NetworkX
        G = nx.DiGraph()
        root_node = f"root_{project_id}"
        G.add_node(root_node, name=project.name, is_root=True)

        package_ids = [d.package_id for d in deps]
        packages_map = {
            pkg.id: pkg.name
            for pkg in db.query(Package).filter(Package.id.in_(package_ids)).all()
        }

        # Query all package vulnerabilities
        pkg_vulns = (
            db.query(PackageVulnerability, Vulnerability)
            .join(Vulnerability, PackageVulnerability.vulnerability_id == Vulnerability.id)
            .filter(PackageVulnerability.package_id.in_(package_ids))
            .all()
        )

        vuln_by_pkg_id: Dict[str, List[Vulnerability]] = {}
        for pv, v in pkg_vulns:
            vuln_by_pkg_id.setdefault(pv.package_id, []).append(v)

        for dep in deps:
            pkg_name = packages_map.get(dep.package_id, "unknown")
            G.add_node(
                dep.package_id,
                name=pkg_name,
                is_direct=dep.is_direct,
                version=dep.resolved_version,
                is_root=False
            )
            if dep.is_direct or not dep.parent_package_id:
                G.add_edge(root_node, dep.package_id)
            else:
                G.add_edge(dep.parent_package_id, dep.package_id)

        # 3. Calculate Depths via Shortest Paths
        depths: Dict[str, int] = {}
        max_depth = 1
        for dep in deps:
            try:
                depth = nx.shortest_path_length(G, source=root_node, target=dep.package_id)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                depth = 1 if dep.is_direct else 2
            depths[dep.package_id] = depth
            max_depth = max(max_depth, depth)

        # 4. Vulnerability Propagation & Reverse Traversal
        vulnerable_packages_info = []
        direct_vuln_count = 0
        transitive_vuln_count = 0
        max_pkg_risk = 0.0
        total_vuln_score = 0.0

        reverse_G = G.reverse()

        for dep in deps:
            vulns = vuln_by_pkg_id.get(dep.package_id, [])
            if not vulns:
                continue

            pkg_name = packages_map.get(dep.package_id, "unknown")
            depth = depths.get(dep.package_id, 1)
            is_direct = dep.is_direct

            if is_direct:
                direct_vuln_count += len(vulns)
            else:
                transitive_vuln_count += len(vulns)

            # Find all upstream dependent packages in this project
            upstream_nodes = set()
            try:
                upstream_nodes = nx.descendants(reverse_G, dep.package_id)
                upstream_nodes.discard(root_node)
            except Exception:
                pass

            upstream_pkg_names = [packages_map.get(n) for n in upstream_nodes if n in packages_map]

            # Cross-project affected count across the organization
            other_projects_count = (
                db.query(Dependency.project_id)
                .filter(Dependency.package_id == dep.package_id)
                .distinct()
                .count()
            )

            # Compute individual package vulnerability risk
            for v in vulns:
                base_sev_score = 50.0
                if v.severity == "CRITICAL":
                    base_sev_score = 95.0
                elif v.severity == "HIGH":
                    base_sev_score = 75.0
                elif v.severity == "MEDIUM":
                    base_sev_score = 50.0
                elif v.severity == "LOW":
                    base_sev_score = 25.0

                if v.cvss_score:
                    base_sev_score = max(base_sev_score, v.cvss_score * 10.0)

                # Depth damping: depth 1 has multiplier 1.0, depth 2 -> 0.85, depth 3 -> 0.70
                depth_factor = max(0.5, 1.0 - 0.15 * (depth - 1))

                # Propagation multiplier based on cross-project usage
                prop_multiplier = 1.0 + min(0.4, (other_projects_count - 1) * 0.1)

                pkg_risk = min(100.0, base_sev_score * depth_factor * prop_multiplier)
                max_pkg_risk = max(max_pkg_risk, pkg_risk)
                total_vuln_score += pkg_risk

                vulnerable_packages_info.append({
                    "package_id": dep.package_id,
                    "package_name": pkg_name,
                    "version": dep.resolved_version,
                    "is_direct": is_direct,
                    "depth": depth,
                    "osv_id": v.osv_id,
                    "cve_id": v.cve_id,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                    "summary": v.summary,
                    "fixed_version": v.fixed_version,
                    "affected_projects_count": other_projects_count,
                    "upstream_dependents": upstream_pkg_names,
                    "calculated_risk": round(pkg_risk, 1)
                })

        # 5. Critical Dependencies & Single Points of Failure (SPOF)
        betweenness = nx.betweenness_centrality(G)
        in_degrees = dict(G.in_degree())

        critical_deps = []
        spof_list = []

        # Find packages with organization-wide criticality
        all_pkg_project_counts: Dict[str, int] = {}
        pkg_counts = (
            db.query(Dependency.package_id, Dependency.project_id)
            .distinct()
            .all()
        )
        for p_id, prj_id in pkg_counts:
            all_pkg_project_counts[p_id] = all_pkg_project_counts.get(p_id, 0) + 1

        for dep in deps:
            pkg_id = dep.package_id
            pkg_name = packages_map.get(pkg_id, "unknown")
            org_projects_count = all_pkg_project_counts.get(pkg_id, 1)
            b_score = betweenness.get(pkg_id, 0.0)
            in_deg = in_degrees.get(pkg_id, 0)
            has_vulns = pkg_id in vuln_by_pkg_id

            # Classification criteria for Critical Dependency:
            # - Used across 2 or more projects, or
            # - High betweenness centrality in project graph (> 0.05)
            is_critical = org_projects_count >= 2 or b_score > 0.05
            
            # Classification criteria for Single Point of Failure (SPOF):
            # - Critical dependency AND contains unpatched vulnerability OR has high downstream dependents
            is_spof = (is_critical and has_vulns) or (in_deg > 1 and org_projects_count >= 2)

            reason_parts = []
            if org_projects_count >= 2:
                reason_parts.append(f"Shared across {org_projects_count} organization projects")
            if b_score > 0.05:
                reason_parts.append(f"High graph betweenness centrality ({round(b_score, 3)})")
            if has_vulns:
                reason_parts.append("Contains known active vulnerability")
            if in_deg > 1:
                reason_parts.append(f"Required by {in_deg} internal packages")

            reason = "; ".join(reason_parts) if reason_parts else "Standard project dependency"

            if is_critical:
                critical_deps.append({
                    "package_name": pkg_name,
                    "affected_projects_count": org_projects_count,
                    "dependency_depth": depths.get(pkg_id, 1),
                    "is_direct": dep.is_direct,
                    "betweenness": round(b_score, 4),
                    "reason": reason
                })

            if is_spof:
                spof_list.append({
                    "package_name": pkg_name,
                    "affected_projects_count": org_projects_count,
                    "dependency_depth": depths.get(pkg_id, 1),
                    "has_vulnerability": has_vulns,
                    "severity": vuln_by_pkg_id[pkg_id][0].severity if has_vulns else "NONE",
                    "reason": f"SPOF: {reason}"
                })

        # 6. Composite 0-100 Risk Score Calculation
        # Weights:
        # - Peak Vulnerability Severity: 45%
        # - Aggregate Vulnerability Volume & Propagation: 25%
        # - Critical Dependencies & SPOF Penalty: 20%
        # - Graph Depth Footprint: 10%
        if vulnerable_packages_info:
            vuln_component = max_pkg_risk * settings.WEIGHT_SEVERITY
            
            avg_vuln = min(100.0, (total_vuln_score / len(vulnerable_packages_info)))
            prop_component = avg_vuln * settings.WEIGHT_PROPAGATION
            
            spof_penalty = min(100.0, (len(spof_list) * 20.0 + len(critical_deps) * 10.0)) * settings.WEIGHT_CENTRALITY
            depth_penalty = min(100.0, max_depth * 15.0) * settings.WEIGHT_DEPTH

            overall_score = round(min(100.0, vuln_component + prop_component + spof_penalty + depth_penalty), 1)
        else:
            # Baseline hygiene risk: projects with deeper trees carry slightly higher structural complexity
            overall_score = round(min(20.0, 5.0 + max_depth * 2.5), 1)

        # Risk Level Mapping
        if overall_score >= 80.0:
            risk_level = "CRITICAL"
        elif overall_score >= 60.0:
            risk_level = "HIGH"
        elif overall_score >= 35.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "overall_score": overall_score,
            "risk_level": risk_level,
            "max_depth": max_depth,
            "critical_deps_count": len(critical_deps),
            "spof_count": len(spof_list),
            "direct_vulnerabilities": direct_vuln_count,
            "transitive_vulnerabilities": transitive_vuln_count,
            "vulnerable_packages": vulnerable_packages_info,
            "critical_dependencies": critical_deps,
            "single_points_of_failure": spof_list,
            "breakdown": {
                "peak_vulnerability_risk": round(max_pkg_risk, 1),
                "vulnerability_component": round(max_pkg_risk * settings.WEIGHT_SEVERITY, 1),
                "propagation_component": round(min(100.0, total_vuln_score) * settings.WEIGHT_PROPAGATION, 1),
                "depth_footprint": round(max_depth * 15.0 * settings.WEIGHT_DEPTH, 1),
                "spof_penalty": round(min(100.0, len(spof_list) * 20.0) * settings.WEIGHT_CENTRALITY, 1)
            }
        }
