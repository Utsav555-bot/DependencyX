import pytest
from fastapi import HTTPException
from backend.app.database.session import SessionLocal
from backend.app.database.seed_data import init_db
from backend.app.models.entities import User, Organization, OrganizationMember, Project, ActivityLog
from backend.app.core.security import (
    get_password_hash, verify_password, create_access_token, decode_token,
    require_admin, require_developer_or_admin
)
from backend.app.api.projects import list_projects, delete_project
from backend.app.services.parser import PackageLockParser

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_password_hashing_security():
    pwd = "EnterprisePassword@2026!"
    h1 = get_password_hash(pwd)
    h2 = get_password_hash(pwd)
    
    # Salts must be random: same password yields different hashes
    assert h1 != h2
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True
    assert verify_password("WrongPassword123!", h1) is False

def test_jwt_token_security():
    token = create_access_token(subject="usr_test_audit", role="developer")
    payload = decode_token(token)
    assert payload["sub"] == "usr_test_audit"
    assert payload["role"] == "developer"

    # Tampered token must be rejected
    with pytest.raises(HTTPException):
        decode_token(token + "tampered")

def test_rbac_admin_vs_developer(db):
    admin = db.query(User).filter(User.role == "admin").first()
    developer = db.query(User).filter(User.role == "developer").first()

    # Admin passes require_admin
    assert require_admin(admin) == admin

    # Developer fails require_admin with 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        require_admin(developer)
    assert exc.value.status_code == 403

def test_organization_data_isolation(db):
    # Create Org B with User B
    org_b = Organization(id="org_isolation_b", name="Isolation Corp", slug="isolation-corp")
    user_b = User(id="usr_b_01", email="user_b@isolation.com", hashed_password="pwd", full_name="User B", role="developer")
    mem_b = OrganizationMember(id="mem_b_01", organization_id=org_b.id, user_id=user_b.id, role="developer")
    proj_b = Project(id="prj_isolation_b", organization_id=org_b.id, name="Secret App B", created_by=user_b.id)

    db.add_all([org_b, user_b, mem_b, proj_b])
    db.commit()

    # Admin from Org A lists projects -> must NOT see Project B
    admin_a = db.query(User).filter(User.email == "admin@dependencyx.io").first()
    projects_a = list_projects(current_user=admin_a, db=db)
    proj_ids_a = [p.id for p in projects_a]
    assert "prj_isolation_b" not in proj_ids_a, "Cross-tenant data leak: Admin A saw Project B"

    # Cleanup
    db.delete(proj_b)
    db.delete(mem_b)
    db.delete(user_b)
    db.delete(org_b)
    db.commit()

def test_sql_injection_resilience(db):
    admin = db.query(User).filter(User.role == "admin").first()
    injection_payload = "' OR '1'='1"

    # Querying projects with SQL injection payload treats it as literal text, not SQL
    result = db.query(Project).filter(Project.name == injection_payload).all()
    assert len(result) == 0

def test_file_upload_validation():
    # Attempting to parse non-JSON executable payload
    corrupted_data = b"\x4D\x5A\x90\x00\x03\x00\x00\x00"  # MZ header (PE executable)
    with pytest.raises(ValueError, match="Invalid JSON format"):
        PackageLockParser.parse(corrupted_data)

def test_activity_logging_records_events(db):
    logs = db.query(ActivityLog).all()
    assert len(logs) > 0
    actions = [l.action for l in logs]
    assert "AUTH_LOGIN" in actions or "PROJECT_CREATE" in actions
