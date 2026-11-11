import pytest
from backend.app.database.session import SessionLocal
from backend.app.database.seed_data import init_db
from backend.app.risk_engine.risk_calculator import RiskAnalysisEngine

@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_risk_calculation_seeded_project(db_session):
    # prj_ecomm_01 has lodash 4.17.15 (High vuln) and axios 0.21.1 (Medium vuln)
    result = RiskAnalysisEngine.calculate_project_risk("prj_ecomm_01", db_session)

    assert result["overall_score"] >= 0.0 and result["overall_score"] <= 100.0
    assert result["risk_level"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert result["max_depth"] >= 2
    assert len(result["vulnerable_packages"]) > 0

    # Verify reverse propagation traversal
    lodash_vuln = next(v for v in result["vulnerable_packages"] if v["package_name"] == "lodash")
    assert lodash_vuln["severity"] == "HIGH"
    assert "axios" in lodash_vuln["upstream_dependents"]
    assert lodash_vuln["is_direct"] is False  # lodash is transitive via axios in e-commerce
