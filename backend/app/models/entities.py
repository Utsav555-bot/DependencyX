import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def generate_uuid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("usr_"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="developer")  # 'admin', 'developer'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    projects_created = relationship("Project", back_populates="creator")
    scans_initiated = relationship("ScanHistory", back_populates="scanner")
    activities = relationship("ActivityLog", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("org_"))
    name = Column(String(150), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("mem_"))
    organization_id = Column(String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="developer")  # 'admin', 'developer'
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("prj_"))
    organization_id = Column(String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=True)
    ecosystem = Column(String(50), nullable=False, default="npm")
    repository_url = Column(String(500), nullable=True)
    manifest_blob_path = Column(String(1000), nullable=True)
    created_by = Column(String(64), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_project_name"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User", back_populates="projects_created")
    dependencies = relationship("Dependency", back_populates="project", cascade="all, delete-orphan")
    scans = relationship("ScanHistory", back_populates="project", cascade="all, delete-orphan", order_by="desc(ScanHistory.created_at)")
    risk_assessments = relationship("RiskAssessment", back_populates="project", cascade="all, delete-orphan", order_by="desc(RiskAssessment.created_at)")


class Package(Base):
    __tablename__ = "packages"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("pkg_"))
    name = Column(String(255), nullable=False, index=True)
    ecosystem = Column(String(50), nullable=False, default="npm")
    latest_version = Column(String(50), nullable=True)
    description = Column(String(1000), nullable=True)
    license = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("name", "ecosystem", name="uq_package_name_ecosystem"),
    )

    # Relationships
    dependencies = relationship("Dependency", back_populates="package", foreign_keys="Dependency.package_id")
    vulnerabilities = relationship("PackageVulnerability", back_populates="package", cascade="all, delete-orphan")


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("dep_"))
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(String(64), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    version_spec = Column(String(100), nullable=True)
    resolved_version = Column(String(100), nullable=False)
    is_direct = Column(Boolean, nullable=False, default=False)
    dependency_type = Column(String(50), nullable=False, default="dependencies")
    depth = Column(Integer, nullable=False, default=1)
    parent_package_id = Column(String(64), ForeignKey("packages.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="dependencies")
    package = relationship("Package", foreign_keys=[package_id], back_populates="dependencies")
    parent_package = relationship("Package", foreign_keys=[parent_package_id])


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("vuln_"))
    osv_id = Column(String(100), unique=True, nullable=False, index=True)
    cve_id = Column(String(100), nullable=True, index=True)
    ghsa_id = Column(String(100), nullable=True)
    summary = Column(String(1000), nullable=True)
    details = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False, default="MEDIUM")  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    cvss_score = Column(Float, nullable=True)
    affected_ecosystem = Column(String(50), nullable=False, default="npm")
    affected_package = Column(String(255), nullable=False, index=True)
    affected_range = Column(String(500), nullable=True)
    fixed_version = Column(String(100), nullable=True)
    published_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    packages = relationship("PackageVulnerability", back_populates="vulnerability", cascade="all, delete-orphan")


class PackageVulnerability(Base):
    __tablename__ = "package_vulnerabilities"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("pv_"))
    package_id = Column(String(64), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    vulnerability_id = Column(String(64), ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_version = Column(String(100), nullable=False)
    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("package_id", "vulnerability_id", "matched_version", name="uq_pkg_vuln_version"),
    )

    # Relationships
    package = relationship("Package", back_populates="vulnerabilities")
    vulnerability = relationship("Vulnerability", back_populates="packages")


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("scan_"))
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scanned_by = Column(String(64), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")  # 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    total_packages = Column(Integer, nullable=False, default=0)
    vulnerable_packages_count = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    low_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=False, default=0)
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="scans")
    scanner = relationship("User", back_populates="scans_initiated")
    risk_assessment = relationship("RiskAssessment", back_populates="scan", uselist=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("risk_"))
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id = Column(String(64), ForeignKey("scan_history.id"), nullable=True)
    overall_score = Column(Float, nullable=False, default=0.0)  # 0.0 - 100.0
    risk_level = Column(String(50), nullable=False, default="LOW")  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    max_depth = Column(Integer, nullable=False, default=1)
    critical_deps_count = Column(Integer, nullable=False, default=0)
    spof_count = Column(Integer, nullable=False, default=0)
    direct_vulnerabilities = Column(Integer, nullable=False, default=0)
    transitive_vulnerabilities = Column(Integer, nullable=False, default=0)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="risk_assessments")
    scan = relationship("ScanHistory", back_populates="risk_assessment")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("act_"))
    organization_id = Column(String(64), ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(64), nullable=True)
    details = Column(String(1000), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="activities")
    user = relationship("User", back_populates="activities")
