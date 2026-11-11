from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import SessionLocal, engine
from backend.app.database.base import Base
from backend.app.models.entities import (
    User, Organization, OrganizationMember, Project, Package, Dependency,
    Vulnerability, PackageVulnerability, ScanHistory, RiskAssessment, ActivityLog
)
from backend.app.core.security import get_password_hash
from backend.app.core.logging import logger

def init_db(db: Session = None):
    """
    Creates tables if they don't exist, establishes views and triggers,
    and seeds initial data if database is empty.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Create database views if not existing
        view_summary_sql = """
        CREATE VIEW IF NOT EXISTS v_project_risk_summary AS
        SELECT 
            p.id AS project_id,
            p.organization_id,
            p.name AS project_name,
            p.ecosystem,
            p.created_at,
            COALESCE(r.overall_score, 0.0) AS latest_risk_score,
            COALESCE(r.risk_level, 'LOW') AS latest_risk_level,
            COALESCE(r.max_depth, 0) AS max_dependency_depth,
            COALESCE(r.spof_count, 0) AS single_point_of_failures,
            COALESCE(s.vulnerable_packages_count, 0) AS vulnerable_packages_count,
            COALESCE(s.critical_count, 0) AS critical_vuln_count,
            COALESCE(s.high_count, 0) AS high_vuln_count,
            COALESCE(s.medium_count, 0) AS medium_vuln_count,
            COALESCE(s.low_count, 0) AS low_vuln_count,
            s.created_at AS last_scan_date
        FROM projects p
        LEFT JOIN (
            SELECT project_id, overall_score, risk_level, max_depth, spof_count
            FROM risk_assessments
            GROUP BY project_id
            HAVING max(created_at)
        ) r ON p.id = r.project_id
        LEFT JOIN (
            SELECT project_id, vulnerable_packages_count, critical_count, high_count, medium_count, low_count, created_at
            FROM scan_history
            WHERE status = 'COMPLETED'
            GROUP BY project_id
            HAVING max(created_at)
        ) s ON p.id = s.project_id;
        """

        view_vuln_deps_sql = """
        CREATE VIEW IF NOT EXISTS v_vulnerable_dependencies AS
        SELECT 
            d.id AS dependency_id,
            d.project_id,
            p.name AS project_name,
            pkg.name AS package_name,
            d.resolved_version,
            d.is_direct,
            d.depth,
            v.osv_id,
            v.cve_id,
            v.severity,
            v.cvss_score,
            v.summary,
            v.fixed_version
        FROM dependencies d
        JOIN projects p ON d.project_id = p.id
        JOIN packages pkg ON d.package_id = pkg.id
        JOIN package_vulnerabilities pv ON pkg.id = pv.package_id AND d.resolved_version = pv.matched_version
        JOIN vulnerabilities v ON pv.vulnerability_id = v.id;
        """

        trigger_sql = """
        CREATE TRIGGER IF NOT EXISTS trg_audit_project_insert
        AFTER INSERT ON projects
        BEGIN
            INSERT INTO activity_logs (id, organization_id, user_id, action, entity_type, entity_id, details, ip_address, created_at)
            VALUES ('act_trg_' || hex(randomblob(6)), NEW.organization_id, NEW.created_by, 'DB_TRIGGER_PROJECT_CREATE', 'PROJECT', NEW.id, 'Database trigger recorded project: ' || NEW.name, '127.0.0.1', datetime('now'));
        END;
        """

        try:
            db.execute(text(view_summary_sql))
            db.execute(text(view_vuln_deps_sql))
            db.execute(text(trigger_sql))
            db.commit()
            logger.info("Database views (v_project_risk_summary, v_vulnerable_dependencies) and audit trigger verified.")
        except Exception as ve:
            logger.warning(f"Note on views/triggers creation: {ve}")
            db.rollback()
        # Check if users already seeded
        admin_user = db.query(User).filter(User.email == "admin@dependencyx.io").first()
        if not admin_user:
            logger.info("Seeding initial DependencyX administrative and test data...")
            hashed_pw = get_password_hash("Password123!")

            # 1. Organization
            org = Organization(
                id="org_acme_01",
                name="Acme CyberSec Global",
                slug="acme-cybersec",
                description="Enterprise application suite security monitoring"
            )
            db.add(org)
            db.flush()

            # 2. Users
            admin_user = User(
                id="usr_admin_01",
                email="admin@dependencyx.io",
                hashed_password=hashed_pw,
                full_name="Security Administrator",
                role="admin",
                is_active=True
            )
            dev_user = User(
                id="usr_dev_01",
                email="developer@dependencyx.io",
                hashed_password=hashed_pw,
                full_name="Lead Fullstack Developer",
                role="developer",
                is_active=True
            )
            db.add_all([admin_user, dev_user])
            db.flush()

            # 3. Memberships
            m1 = OrganizationMember(id="mem_01", organization_id=org.id, user_id=admin_user.id, role="admin")
            m2 = OrganizationMember(id="mem_02", organization_id=org.id, user_id=dev_user.id, role="developer")
            db.add_all([m1, m2])

            # 4. Master Packages
            p_lodash = Package(id="pkg_lodash", name="lodash", ecosystem="npm", latest_version="4.17.21", description="Lodash modular utilities", license="MIT")
            p_axios = Package(id="pkg_axios", name="axios", ecosystem="npm", latest_version="1.6.8", description="Promise based HTTP client", license="MIT")
            p_express = Package(id="pkg_express", name="express", ecosystem="npm", latest_version="4.19.2", description="Minimalist web framework", license="MIT")
            p_jwt = Package(id="pkg_jwt", name="jsonwebtoken", ecosystem="npm", latest_version="9.0.2", description="JSON Web Token implementation", license="MIT")
            p_react = Package(id="pkg_react", name="react", ecosystem="npm", latest_version="18.2.0", description="React UI library", license="MIT")
            p_cookie = Package(id="pkg_cookie", name="cookie", ecosystem="npm", latest_version="0.7.0", description="Cookie parser", license="MIT")
            p_semver = Package(id="pkg_semver", name="semver", ecosystem="npm", latest_version="7.6.0", description="Semantic versioner", license="ISC")
            db.add_all([p_lodash, p_axios, p_express, p_jwt, p_react, p_cookie, p_semver])
            db.flush()

            # 5. Projects
            p1 = Project(
                id="prj_ecomm_01",
                organization_id=org.id,
                name="Storefront Web App",
                description="Customer facing web shop with product search and checkout",
                ecosystem="npm",
                repository_url="https://github.com/acme/storefront-web",
                created_by=admin_user.id
            )
            p2 = Project(
                id="prj_pay_02",
                organization_id=org.id,
                name="Payment Gateway Integration",
                description="PCI-DSS compliant payment integration microservice",
                ecosystem="npm",
                repository_url="https://github.com/acme/payment-gateway",
                created_by=dev_user.id
            )
            p3 = Project(
                id="prj_notif_03",
                organization_id=org.id,
                name="Cloud Notification Engine",
                description="Event-driven email, SMS and push dispatch worker",
                ecosystem="npm",
                repository_url="https://github.com/acme/notification-engine",
                created_by=dev_user.id
            )
            db.add_all([p1, p2, p3])
            db.flush()

            # 6. Dependencies
            deps = [
                # Storefront Web App
                Dependency(id="dep_01", project_id=p1.id, package_id=p_react.id, version_spec="^18.2.0", resolved_version="18.2.0", is_direct=True, depth=1),
                Dependency(id="dep_02", project_id=p1.id, package_id=p_axios.id, version_spec="^0.21.1", resolved_version="0.21.1", is_direct=True, depth=1),
                Dependency(id="dep_03", project_id=p1.id, package_id=p_lodash.id, version_spec="^4.17.15", resolved_version="4.17.15", is_direct=False, depth=2, parent_package_id=p_axios.id),
                # Payment Gateway
                Dependency(id="dep_04", project_id=p2.id, package_id=p_express.id, version_spec="^4.16.0", resolved_version="4.16.0", is_direct=True, depth=1),
                Dependency(id="dep_05", project_id=p2.id, package_id=p_jwt.id, version_spec="^8.5.1", resolved_version="8.5.1", is_direct=True, depth=1),
                Dependency(id="dep_06", project_id=p2.id, package_id=p_cookie.id, version_spec="^0.3.1", resolved_version="0.3.1", is_direct=False, depth=2, parent_package_id=p_express.id),
                Dependency(id="dep_07", project_id=p2.id, package_id=p_semver.id, version_spec="^5.7.1", resolved_version="5.7.1", is_direct=False, depth=2, parent_package_id=p_jwt.id),
                # Notification Engine
                Dependency(id="dep_08", project_id=p3.id, package_id=p_axios.id, version_spec="^1.6.8", resolved_version="1.6.8", is_direct=True, depth=1),
                Dependency(id="dep_09", project_id=p3.id, package_id=p_lodash.id, version_spec="^4.17.21", resolved_version="4.17.21", is_direct=True, depth=1),
            ]
            db.add_all(deps)
            db.flush()

            # 7. Known OSV Vulnerabilities
            v1 = Vulnerability(
                id="vuln_01",
                osv_id="GHSA-35jh-r3h4-6jhm",
                cve_id="CVE-2020-8203",
                ghsa_id="GHSA-35jh-r3h4-6jhm",
                summary="Prototype Pollution in lodash",
                details="Prototype pollution vulnerability in lodash before 4.17.19 via zipObjectDeep function.",
                severity="HIGH",
                cvss_score=7.4,
                affected_ecosystem="npm",
                affected_package="lodash",
                affected_range="<4.17.19",
                fixed_version="4.17.19"
            )
            v2 = Vulnerability(
                id="vuln_02",
                osv_id="GHSA-42xw-2xvc-cxqx",
                cve_id="CVE-2021-23343",
                ghsa_id="GHSA-42xw-2xvc-cxqx",
                summary="ReDoS in path-to-regexp / axios dependency",
                details="Regular expression denial of service in axios param serializer before 0.21.2.",
                severity="MEDIUM",
                cvss_score=5.3,
                affected_ecosystem="npm",
                affected_package="axios",
                affected_range="<0.21.2",
                fixed_version="0.21.2"
            )
            v3 = Vulnerability(
                id="vuln_03",
                osv_id="GHSA-hjrf-2m68-5959",
                cve_id="CVE-2022-23529",
                ghsa_id="GHSA-hjrf-2m68-5959",
                summary="Remote Code Execution in jsonwebtoken verify()",
                details="Insecure key retrieval allows remote code execution when verifying forged tokens in jsonwebtoken < 9.0.0.",
                severity="CRITICAL",
                cvss_score=9.8,
                affected_ecosystem="npm",
                affected_package="jsonwebtoken",
                affected_range="<9.0.0",
                fixed_version="9.0.0"
            )
            v4 = Vulnerability(
                id="vuln_04",
                osv_id="GHSA-pxg6-pf52-xh8x",
                cve_id="CVE-2024-47764",
                ghsa_id="GHSA-pxg6-pf52-xh8x",
                summary="cookie allows out-of-bounds character parsing",
                details="Cookie parser in cookie prior to 0.7.0 can trigger out of bounds read on corrupted headers.",
                severity="LOW",
                cvss_score=3.7,
                affected_ecosystem="npm",
                affected_package="cookie",
                affected_range="<0.7.0",
                fixed_version="0.7.0"
            )
            db.add_all([v1, v2, v3, v4])
            db.flush()

            # 8. Link Package Vulnerabilities
            pv1 = PackageVulnerability(id="pv_01", package_id=p_lodash.id, vulnerability_id=v1.id, matched_version="4.17.15")
            pv2 = PackageVulnerability(id="pv_02", package_id=p_axios.id, vulnerability_id=v2.id, matched_version="0.21.1")
            pv3 = PackageVulnerability(id="pv_03", package_id=p_jwt.id, vulnerability_id=v3.id, matched_version="8.5.1")
            pv4 = PackageVulnerability(id="pv_04", package_id=p_cookie.id, vulnerability_id=v4.id, matched_version="0.3.1")
            db.add_all([pv1, pv2, pv3, pv4])

            # 9. Scan History
            s1 = ScanHistory(id="scan_01", project_id=p1.id, scanned_by=admin_user.id, status="COMPLETED", total_packages=3, vulnerable_packages_count=2, critical_count=0, high_count=1, medium_count=1, low_count=0, duration_ms=1420)
            s2 = ScanHistory(id="scan_02", project_id=p2.id, scanned_by=dev_user.id, status="COMPLETED", total_packages=4, vulnerable_packages_count=2, critical_count=1, high_count=0, medium_count=0, low_count=1, duration_ms=1850)
            s3 = ScanHistory(id="scan_03", project_id=p3.id, scanned_by=dev_user.id, status="COMPLETED", total_packages=2, vulnerable_packages_count=0, critical_count=0, high_count=0, medium_count=0, low_count=0, duration_ms=680)
            db.add_all([s1, s2, s3])

            # 10. Risk Assessments
            r1 = RiskAssessment(id="risk_01", project_id=p1.id, scan_id=s1.id, overall_score=68.5, risk_level="HIGH", max_depth=2, critical_deps_count=1, spof_count=1, direct_vulnerabilities=1, transitive_vulnerabilities=1)
            r2 = RiskAssessment(id="risk_02", project_id=p2.id, scan_id=s2.id, overall_score=92.0, risk_level="CRITICAL", max_depth=2, critical_deps_count=2, spof_count=1, direct_vulnerabilities=1, transitive_vulnerabilities=1)
            r3 = RiskAssessment(id="risk_03", project_id=p3.id, scan_id=s3.id, overall_score=12.0, risk_level="LOW", max_depth=1, critical_deps_count=0, spof_count=0, direct_vulnerabilities=0, transitive_vulnerabilities=0)
            db.add_all([r1, r2, r3])

            # 11. Activity Logs
            a1 = ActivityLog(id="act_01", organization_id=org.id, user_id=admin_user.id, action="AUTH_LOGIN", entity_type="USER", entity_id=admin_user.id, details="User admin@dependencyx.io logged in")
            a2 = ActivityLog(id="act_02", organization_id=org.id, user_id=admin_user.id, action="PROJECT_CREATE", entity_type="PROJECT", entity_id=p1.id, details=f"Created project {p1.name}")
            a3 = ActivityLog(id="act_03", organization_id=org.id, user_id=admin_user.id, action="VULN_SCAN", entity_type="SCAN", entity_id=s1.id, details="Completed OSV vulnerability scan: 2 vulnerable packages")
            db.add_all([a1, a2, a3])

            db.commit()
            logger.info("Database successfully seeded with realistic sample data!")
        else:
            logger.info("Database already initialized and contains user accounts.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {str(e)}")
        raise
    finally:
        if close_session:
            db.close()

if __name__ == "__main__":
    init_db()
