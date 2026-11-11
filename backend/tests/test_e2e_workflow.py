import pytest
import io
import asyncio
from fastapi import UploadFile
from backend.app.database.session import SessionLocal
from backend.app.database.seed_data import init_db
from backend.app.models.entities import User, Project, Dependency, Package, Vulnerability, ScanHistory, RiskAssessment
from backend.app.api.auth import login
from backend.app.schemas.all_schemas import UserLogin, ProjectCreate
from backend.app.api.projects import create_project, get_project
from backend.app.api.dependencies import upload_package_manifest, get_dependency_graph, get_project_dependencies
from backend.app.api.vulnerabilities import trigger_vulnerability_scan, get_project_vulnerabilities
from backend.app.api.risk import get_project_risk_assessment
from backend.app.api.analytics import get_dashboard_analytics
from backend.app.api.reports import export_report, get_html_report

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_complete_e2e_workflow(db):
    async def _workflow():
        print("\n--- BEGIN PHASE 2: END-TO-END WORKFLOW AUDIT ---")

        # STEP 1: Log in as a developer
        login_req = UserLogin(email="developer@dependencyx.io", password="Password123!")
        auth_resp = login(login_req, db)
        assert auth_resp.access_token is not None
        assert auth_resp.role == "developer"
        dev_user = db.query(User).filter(User.id == auth_resp.user_id).first()
        print(f"STEP 1 PASSED: Logged in as developer: {dev_user.email} (ID: {dev_user.id})")

        # STEP 2: Create a new project
        proj_name = "Audit Microservice E2E"
        existing = db.query(Project).filter(Project.name == proj_name).first()
        if existing:
            db.delete(existing)
            db.commit()

        proj_in = ProjectCreate(
            name=proj_name,
            description="End-to-End Audit Target Application",
            ecosystem="npm",
            repository_url="https://github.com/acme/audit-microservice"
        )
        new_project = create_project(proj_in, current_user=dev_user, db=db)
        assert new_project.id is not None
        assert new_project.name == proj_name
        print(f"STEP 2 PASSED: Created project '{new_project.name}' (ID: {new_project.id})")

        # STEP 3: Upload a real package-lock.json file
        with open("backend/samples/sample_vulnerable_lock.json", "rb") as f:
            file_bytes = f.read()

        upload_file_obj = UploadFile(
            file=io.BytesIO(file_bytes),
            filename="package-lock.json",
            headers={"content-type": "application/json"}
        )
        upload_res = await upload_package_manifest(new_project.id, upload_file_obj, current_user=dev_user, db=db)
        assert upload_res["total_packages"] >= 10
        assert upload_res["total_dependencies"] >= 10
        print(f"STEP 3 PASSED: Uploaded real package-lock.json (Lockfile v{upload_res['lockfile_version']})")

        # STEP 4: Verify packages are extracted
        extracted_deps = get_project_dependencies(new_project.id, current_user=dev_user, db=db)
        extracted_names = [d.package_name for d in extracted_deps]
        assert "axios" in extracted_names
        assert "express" in extracted_names
        assert "jsonwebtoken" in extracted_names
        assert "lodash" in extracted_names
        print(f"STEP 4 PASSED: Extracted {len(extracted_deps)} packages: {', '.join(extracted_names[:6])}...")

        # STEP 5: Verify dependency relationships are stored
        direct_deps = [d for d in extracted_deps if d.is_direct]
        transitive_deps = [d for d in extracted_deps if not d.is_direct]
        assert len(direct_deps) >= 3
        assert len(transitive_deps) >= 5
        print(f"STEP 5 PASSED: Relationships stored ({len(direct_deps)} direct, {len(transitive_deps)} transitive)")

        # STEP 6: Open the dependency graph
        graph_res = get_dependency_graph(new_project.id, current_user=dev_user, db=db)
        assert len(graph_res["nodes"]) >= 10
        assert len(graph_res["edges"]) >= 9
        print(f"STEP 6 PASSED: Dependency graph generated with {len(graph_res['nodes'])} nodes and {len(graph_res['edges'])} edges")

        # STEP 7: Verify direct and transitive dependencies in graph
        root_node = next(n for n in graph_res["nodes"] if n["data"].get("node_type") == "project_root")
        assert root_node["data"]["label"] == proj_name
        depth_dist = graph_res["summary"]["depth_distribution"]
        assert depth_dist.get(1, 0) >= 3  # Level 1 direct
        assert depth_dist.get(2, 0) >= 5  # Level 2 transitive
        print(f"STEP 7 PASSED: Graph verified: Depth 1 (Direct) = {depth_dist.get(1)}, Depth 2 (Transitive) = {depth_dist.get(2)}")

        # STEP 8: Run an OSV vulnerability scan
        scan_res = await trigger_vulnerability_scan(new_project.id, current_user=dev_user, db=db)
        assert scan_res["status"] == "COMPLETED"
        assert scan_res["total_packages_scanned"] >= 10
        print(f"STEP 8 PASSED: OSV vulnerability scan completed in {scan_res['duration_ms']}ms")

        # STEP 9: Verify actual vulnerability results
        vulns = get_project_vulnerabilities(new_project.id, current_user=dev_user, db=db)
        assert len(vulns) >= 2, "Expected vulnerabilities in sample manifest"
        cve_list = [v.cve_id or v.osv_id for v in vulns]
        print(f"STEP 9 PASSED: Verified {len(vulns)} real vulnerabilities detected: {', '.join(cve_list)}")

        # STEP 10 & 11: Open risk analysis & verify metrics
        risk = get_project_risk_assessment(new_project.id, current_user=dev_user, db=db)
        assert risk.overall_score > 0.0 and risk.overall_score <= 100.0
        assert risk.risk_level in ["CRITICAL", "HIGH", "MEDIUM"]
        assert risk.max_depth >= 2
        assert len(risk.vulnerable_packages) > 0
        has_propagation = any(len(vp.get("upstream_dependents", [])) > 0 or not vp.get("is_direct") for vp in risk.vulnerable_packages)
        assert has_propagation
        print(f"STEP 10 & 11 PASSED: Risk Score = {risk.overall_score}/100 ({risk.risk_level}), Max Depth = {risk.max_depth}, SPOF Count = {risk.spof_count}")

        # STEP 12: Verify dashboard metrics update
        analytics = get_dashboard_analytics(current_user=dev_user, db=db)
        assert analytics.metrics.total_projects >= 4
        assert any(p["project_name"] == proj_name for p in analytics.project_risk_comparison)
        print(f"STEP 12 PASSED: Dashboard analytics reflects {analytics.metrics.total_projects} total projects, overall org risk = {analytics.metrics.overall_org_risk_score}")

        # STEP 13: Generate and download security reports
        csv_resp = export_report(new_project.id, format="csv", current_user=dev_user, db=db)
        csv_content = csv_resp.body.decode("utf-8")
        assert "DependencyX Security Audit Report" in csv_content
        assert proj_name in csv_content
        assert "axios" in csv_content

        html_resp = get_html_report(new_project.id, current_user=dev_user, db=db)
        html_content = html_resp.body.decode("utf-8")
        assert "DependencyX" in html_content
        assert proj_name in html_content
        print("STEP 13 PASSED: CSV and HTML security reports successfully generated and validated")
        print("--- COMPLETE END-TO-END WORKFLOW AUDIT VERIFIED 100% SUCCESS ---")

    asyncio.run(_workflow())
