import pytest
from sqlalchemy import text
from backend.app.database.session import SessionLocal
from backend.app.database.seed_data import init_db
from backend.app.models.entities import (
    User, Organization, OrganizationMember, Project, Package,
    Dependency, Vulnerability, PackageVulnerability, ScanHistory,
    RiskAssessment, ActivityLog
)

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_all_11_tables_exist(db):
    expected_tables = {
        "users", "organizations", "organization_members", "projects",
        "packages", "dependencies", "vulnerabilities", "package_vulnerabilities",
        "scan_history", "risk_assessments", "activity_logs"
    }
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    existing_tables = {r[0] for r in result}
    assert expected_tables.issubset(existing_tables), f"Missing tables: {expected_tables - existing_tables}"

def test_database_views(db):
    # Test View 1: v_project_risk_summary
    v1_rows = db.execute(text("SELECT project_id, project_name, latest_risk_score, latest_risk_level FROM v_project_risk_summary")).fetchall()
    assert len(v1_rows) >= 3, "View v_project_risk_summary returned no rows"

    # Test View 2: v_vulnerable_dependencies
    v2_rows = db.execute(text("SELECT project_name, package_name, resolved_version, severity FROM v_vulnerable_dependencies")).fetchall()
    assert len(v2_rows) >= 3, "View v_vulnerable_dependencies returned no rows"

def test_database_trigger(db):
    # Insert temporary project to test trigger
    test_prj_id = "prj_trigger_audit_test"
    db.execute(text(f"""
        INSERT INTO projects (id, organization_id, name, description, ecosystem, created_by, created_at, updated_at)
        VALUES ('{test_prj_id}', 'org_acme_01', 'Audit Trigger Test', 'Testing trigger', 'npm', 'usr_admin_01', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """))
    db.commit()

    # Verify trigger inserted record into activity_logs
    trg_log = db.execute(text(f"SELECT action, details FROM activity_logs WHERE entity_id = '{test_prj_id}' AND action = 'DB_TRIGGER_PROJECT_CREATE'")).fetchone()
    assert trg_log is not None, "Database trigger trg_audit_project_insert failed to record audit entry"

    # Cleanup
    db.execute(text(f"DELETE FROM projects WHERE id = '{test_prj_id}'"))
    db.execute(text(f"DELETE FROM activity_logs WHERE entity_id = '{test_prj_id}'"))
    db.commit()

def test_indexes_exist(db):
    indexes = db.execute(text("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")).fetchall()
    index_names = [i[0] for i in indexes]
    # Check that indices exist on packages, dependencies, vulnerabilities
    assert any("package" in name.lower() or "pkg" in name.lower() for name in index_names)
    assert any("depend" in name.lower() or "dep" in name.lower() for name in index_names)

def test_transaction_acid_rollback(db):
    # Test atomic transaction rollback on failure
    try:
        with db.begin_nested():
            db.execute(text("INSERT INTO projects (id, organization_id, name, created_by) VALUES ('prj_fail_test', 'org_acme_01', 'Fail Test', 'usr_admin_01')"))
            # Intentionally cause foreign key violation or duplicate primary key
            db.execute(text("INSERT INTO projects (id, organization_id, name, created_by) VALUES ('prj_fail_test', 'org_acme_01', 'Fail Duplicate', 'usr_admin_01')"))
    except Exception:
        pass  # Expected rollback

    # Verify rollback
    rolled_back = db.execute(text("SELECT id FROM projects WHERE id = 'prj_fail_test'")).fetchone()
    assert rolled_back is None, "Transaction failed to roll back on error"
