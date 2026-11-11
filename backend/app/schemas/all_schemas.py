from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# ----------------- AUTH SCHEMAS -----------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = "developer"  # 'admin' or 'developer'
    organization_name: Optional[str] = "Default Organization"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- PROJECT SCHEMAS -----------------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    ecosystem: Optional[str] = "npm"
    repository_url: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    ecosystem: str
    repository_url: Optional[str] = None
    manifest_blob_path: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    # Aggregated metrics for easy display
    total_dependencies: Optional[int] = 0
    vulnerable_packages_count: Optional[int] = 0
    risk_score: Optional[float] = 0.0
    risk_level: Optional[str] = "LOW"

    model_config = ConfigDict(from_attributes=True)

# ----------------- DEPENDENCY & GRAPH SCHEMAS -----------------
class DependencyItem(BaseModel):
    id: str
    package_name: str
    resolved_version: str
    is_direct: bool
    dependency_type: str
    depth: int
    parent_package_name: Optional[str] = None
    has_vulnerability: Optional[bool] = False
    highest_severity: Optional[str] = "NONE"

class GraphResponse(BaseModel):
    root_node_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    summary: Dict[str, Any]

# ----------------- VULNERABILITY SCHEMAS -----------------
class VulnerabilityItem(BaseModel):
    id: str
    osv_id: str
    cve_id: Optional[str] = None
    ghsa_id: Optional[str] = None
    summary: Optional[str] = None
    details: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    affected_package: str
    affected_range: Optional[str] = None
    fixed_version: Optional[str] = None
    published_at: Optional[datetime] = None

class ScanHistoryResponse(BaseModel):
    id: str
    project_id: str
    status: str
    total_packages: int
    vulnerable_packages_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    duration_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- RISK SCHEMAS -----------------
class RiskDetailsResponse(BaseModel):
    project_id: str
    project_name: str
    overall_score: float
    risk_level: str
    max_depth: int
    critical_deps_count: int
    spof_count: int
    direct_vulnerabilities: int
    transitive_vulnerabilities: int
    vulnerable_packages: List[Dict[str, Any]]
    critical_dependencies: List[Dict[str, Any]]
    single_points_of_failure: List[Dict[str, Any]]
    breakdown: Dict[str, Any]

class CriticalDependencyItem(BaseModel):
    package_name: str
    affected_projects_count: int
    dependency_depth: int
    is_direct: bool
    reason: str
    highest_severity: Optional[str] = "NONE"

# ----------------- DASHBOARD ANALYTICS SCHEMAS -----------------
class DashboardMetrics(BaseModel):
    total_projects: int
    total_unique_packages: int
    total_dependencies: int
    vulnerable_packages: int
    critical_vulnerabilities: int
    high_risk_projects: int
    affected_projects: int
    overall_org_risk_score: float

class SeverityDistribution(BaseModel):
    severity: str
    count: int

class DepthDistribution(BaseModel):
    depth: int
    count: int

class DashboardAnalyticsResponse(BaseModel):
    metrics: DashboardMetrics
    severity_distribution: List[SeverityDistribution]
    top_vulnerable_packages: List[Dict[str, Any]]
    project_risk_comparison: List[Dict[str, Any]]
    depth_distribution: List[DepthDistribution]
    recent_activity: List[Dict[str, Any]]
    latest_alerts: List[Dict[str, Any]]
