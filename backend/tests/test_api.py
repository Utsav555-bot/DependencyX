import pytest
from backend.app.database.session import SessionLocal
from backend.app.database.seed_data import init_db
from backend.app.models.entities import User
from backend.app.api.projects import list_projects, get_project
from backend.app.api.dependencies import get_project_dependencies, get_dependency_graph
from backend.app.api.risk import get_project_risk_assessment, get_organization_risk, get_critical_dependencies
from backend.app.api.analytics import get_dashboard_analytics
from backend.app.api.reports import export_report, get_html_report
from backend.app.api.activity import get_activity_logs

@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def admin_user(db_session):
    return db_session.query(User).filter(User.email == "admin@dependencyx.io").first()

def test_list_and_get_projects(db_session, admin_user):
    projects = list_projects(current_user=admin_user, db=db_session)
    assert len(projects) >= 3
    
    first_prj = projects[0]
    fetched = get_project(first_prj.id, current_user=admin_user, db=db_session)
    assert fetched.id == first_prj.id
    assert fetched.name == first_prj.name

def test_dependencies_and_graph(db_session, admin_user):
    deps = get_project_dependencies("prj_ecomm_01", current_user=admin_user, db=db_session)
    assert len(deps) >= 3

    graph = get_dependency_graph("prj_ecomm_01", current_user=admin_user, db=db_session)
    assert len(graph["nodes"]) >= 3
    assert len(graph["edges"]) >= 2
    assert "summary" in graph

def test_risk_and_critical_deps(db_session, admin_user):
    risk = get_project_risk_assessment("prj_ecomm_01", current_user=admin_user, db=db_session)
    assert risk.overall_score >= 0.0
    assert risk.risk_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    org_risk = get_organization_risk(current_user=admin_user, db=db_session)
    assert org_risk["total_projects"] >= 3

    crit_deps = get_critical_dependencies(current_user=admin_user, db=db_session)
    assert isinstance(crit_deps, list)

def test_dashboard_analytics(db_session, admin_user):
    analytics = get_dashboard_analytics(current_user=admin_user, db=db_session)
    assert analytics.metrics.total_projects >= 3
    assert analytics.metrics.total_dependencies >= 5
    assert len(analytics.severity_distribution) == 4
    assert len(analytics.project_risk_comparison) >= 3

def test_reports_generation(db_session, admin_user):
    html_res = get_html_report("prj_ecomm_01", current_user=admin_user, db=db_session)
    assert "DependencyX" in html_res.body.decode("utf-8")

    csv_res = export_report("prj_ecomm_01", format="csv", current_user=admin_user, db=db_session)
    csv_text = csv_res.body.decode("utf-8")
    assert "Package Name,Resolved Version" in csv_text
    assert "lodash" in csv_text

def test_activity_logs(db_session, admin_user):
    logs = get_activity_logs(limit=10, current_user=admin_user, db=db_session)
    assert len(logs) > 0
    assert "action" in logs[0]
