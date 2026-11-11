-- =====================================================================
-- DependencyX - Software Dependency Risk Map
-- Relational Database Management System (RDBMS) Schema Script
-- Compatible with: Microsoft Azure SQL Database / Microsoft SQL Server
-- Normalized to Third Normal Form (3NF)
-- =====================================================================

-- Drop existing views and tables in reverse dependency order if rerunning
IF OBJECT_ID('dbo.v_project_risk_summary', 'V') IS NOT NULL DROP VIEW dbo.v_project_risk_summary;
IF OBJECT_ID('dbo.v_vulnerable_dependencies', 'V') IS NOT NULL DROP VIEW dbo.v_vulnerable_dependencies;
IF OBJECT_ID('dbo.sp_calculate_project_risk_metrics', 'P') IS NOT NULL DROP PROCEDURE dbo.sp_calculate_project_risk_metrics;

IF OBJECT_ID('dbo.activity_logs', 'U') IS NOT NULL DROP TABLE dbo.activity_logs;
IF OBJECT_ID('dbo.risk_assessments', 'U') IS NOT NULL DROP TABLE dbo.risk_assessments;
IF OBJECT_ID('dbo.scan_history', 'U') IS NOT NULL DROP TABLE dbo.scan_history;
IF OBJECT_ID('dbo.package_vulnerabilities', 'U') IS NOT NULL DROP TABLE dbo.package_vulnerabilities;
IF OBJECT_ID('dbo.vulnerabilities', 'U') IS NOT NULL DROP TABLE dbo.vulnerabilities;
IF OBJECT_ID('dbo.dependencies', 'U') IS NOT NULL DROP TABLE dbo.dependencies;
IF OBJECT_ID('dbo.packages', 'U') IS NOT NULL DROP TABLE dbo.packages;
IF OBJECT_ID('dbo.projects', 'U') IS NOT NULL DROP TABLE dbo.projects;
IF OBJECT_ID('dbo.organization_members', 'U') IS NOT NULL DROP TABLE dbo.organization_members;
IF OBJECT_ID('dbo.organizations', 'U') IS NOT NULL DROP TABLE dbo.organizations;
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL DROP TABLE dbo.users;

-- =====================================================================
-- 1. USERS TABLE
-- Stores system users, credentials, global roles, and status
-- =====================================================================
CREATE TABLE dbo.users (
    id NVARCHAR(64) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    hashed_password NVARCHAR(255) NOT NULL,
    full_name NVARCHAR(150) NOT NULL,
    role NVARCHAR(50) NOT NULL DEFAULT 'developer', -- 'admin', 'developer'
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_users PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_user_role CHECK (role IN ('admin', 'developer'))
);

-- =====================================================================
-- 2. ORGANIZATIONS TABLE
-- Multi-tenant organizational isolation
-- =====================================================================
CREATE TABLE dbo.organizations (
    id NVARCHAR(64) NOT NULL,
    name NVARCHAR(150) NOT NULL,
    slug NVARCHAR(100) NOT NULL,
    description NVARCHAR(500) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_organizations PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_organizations_slug UNIQUE (slug)
);

-- =====================================================================
-- 3. ORGANIZATION_MEMBERS TABLE
-- Junction table mapping Users to Organizations with Role-Based Access
-- =====================================================================
CREATE TABLE dbo.organization_members (
    id NVARCHAR(64) NOT NULL,
    organization_id NVARCHAR(64) NOT NULL,
    user_id NVARCHAR(64) NOT NULL,
    role NVARCHAR(50) NOT NULL DEFAULT 'developer', -- 'admin', 'developer'
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_organization_members PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_org_user UNIQUE (organization_id, user_id),
    CONSTRAINT fk_org_members_org FOREIGN KEY (organization_id) 
        REFERENCES dbo.organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_org_members_user FOREIGN KEY (user_id) 
        REFERENCES dbo.users(id) ON DELETE CASCADE,
    CONSTRAINT chk_org_member_role CHECK (role IN ('admin', 'developer'))
);

-- =====================================================================
-- 4. PROJECTS TABLE
-- Software applications tracked for dependency risk mapping
-- =====================================================================
CREATE TABLE dbo.projects (
    id NVARCHAR(64) NOT NULL,
    organization_id NVARCHAR(64) NOT NULL,
    name NVARCHAR(150) NOT NULL,
    description NVARCHAR(1000) NULL,
    ecosystem NVARCHAR(50) NOT NULL DEFAULT 'npm',
    repository_url NVARCHAR(500) NULL,
    manifest_blob_path NVARCHAR(1000) NULL, -- Azure Blob Storage reference
    created_by NVARCHAR(64) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_projects PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_org_project_name UNIQUE (organization_id, name),
    CONSTRAINT fk_projects_org FOREIGN KEY (organization_id) 
        REFERENCES dbo.organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_projects_user FOREIGN KEY (created_by) 
        REFERENCES dbo.users(id)
);

-- =====================================================================
-- 5. PACKAGES TABLE
-- Master catalog of unique software packages across the ecosystem
-- =====================================================================
CREATE TABLE dbo.packages (
    id NVARCHAR(64) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    ecosystem NVARCHAR(50) NOT NULL DEFAULT 'npm',
    latest_version NVARCHAR(50) NULL,
    description NVARCHAR(1000) NULL,
    license NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_packages PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_package_name_ecosystem UNIQUE (name, ecosystem)
);

-- =====================================================================
-- 6. DEPENDENCIES TABLE
-- Manifest dependency edges connecting projects and resolved packages
-- Includes tree depth, direct/transitive flag, and parent package pointer
-- =====================================================================
CREATE TABLE dbo.dependencies (
    id NVARCHAR(64) NOT NULL,
    project_id NVARCHAR(64) NOT NULL,
    package_id NVARCHAR(64) NOT NULL,
    version_spec NVARCHAR(100) NULL,
    resolved_version NVARCHAR(100) NOT NULL,
    is_direct BIT NOT NULL DEFAULT 0,
    dependency_type NVARCHAR(50) NOT NULL DEFAULT 'dependencies', -- 'dependencies', 'devDependencies', 'peerDependencies'
    depth INT NOT NULL DEFAULT 1,
    parent_package_id NVARCHAR(64) NULL, -- Points to immediate parent package in the dependency graph
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_dependencies PRIMARY KEY CLUSTERED (id),
    CONSTRAINT fk_deps_project FOREIGN KEY (project_id) 
        REFERENCES dbo.projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_deps_package FOREIGN KEY (package_id) 
        REFERENCES dbo.packages(id) ON DELETE CASCADE,
    CONSTRAINT fk_deps_parent FOREIGN KEY (parent_package_id) 
        REFERENCES dbo.packages(id)
);

-- =====================================================================
-- 7. VULNERABILITIES TABLE
-- Known CVE / GHSA / OSV security vulnerabilities
-- =====================================================================
CREATE TABLE dbo.vulnerabilities (
    id NVARCHAR(64) NOT NULL,
    osv_id NVARCHAR(100) NOT NULL,
    cve_id NVARCHAR(100) NULL,
    ghsa_id NVARCHAR(100) NULL,
    summary NVARCHAR(1000) NULL,
    details NVARCHAR(MAX) NULL,
    severity NVARCHAR(50) NOT NULL DEFAULT 'MEDIUM', -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    cvss_score FLOAT NULL,
    affected_ecosystem NVARCHAR(50) NOT NULL DEFAULT 'npm',
    affected_package NVARCHAR(255) NOT NULL,
    affected_range NVARCHAR(500) NULL,
    fixed_version NVARCHAR(100) NULL,
    published_at DATETIME2 NULL,
    retrieved_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_vulnerabilities PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_vulnerabilities_osv UNIQUE (osv_id),
    CONSTRAINT chk_severity CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'))
);

-- =====================================================================
-- 8. PACKAGE_VULNERABILITIES TABLE
-- Junction table linking packages and matched vulnerabilities
-- =====================================================================
CREATE TABLE dbo.package_vulnerabilities (
    id NVARCHAR(64) NOT NULL,
    package_id NVARCHAR(64) NOT NULL,
    vulnerability_id NVARCHAR(64) NOT NULL,
    matched_version NVARCHAR(100) NOT NULL,
    detected_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_package_vulnerabilities PRIMARY KEY CLUSTERED (id),
    CONSTRAINT uq_pkg_vuln UNIQUE (package_id, vulnerability_id, matched_version),
    CONSTRAINT fk_pkg_vuln_pkg FOREIGN KEY (package_id) 
        REFERENCES dbo.packages(id) ON DELETE CASCADE,
    CONSTRAINT fk_pkg_vuln_vuln FOREIGN KEY (vulnerability_id) 
        REFERENCES dbo.vulnerabilities(id) ON DELETE CASCADE
);

-- =====================================================================
-- 9. SCAN_HISTORY TABLE
-- Audit log of dependency vulnerability scans per project
-- =====================================================================
CREATE TABLE dbo.scan_history (
    id NVARCHAR(64) NOT NULL,
    project_id NVARCHAR(64) NOT NULL,
    scanned_by NVARCHAR(64) NOT NULL,
    status NVARCHAR(50) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    total_packages INT NOT NULL DEFAULT 0,
    vulnerable_packages_count INT NOT NULL DEFAULT 0,
    critical_count INT NOT NULL DEFAULT 0,
    high_count INT NOT NULL DEFAULT 0,
    medium_count INT NOT NULL DEFAULT 0,
    low_count INT NOT NULL DEFAULT 0,
    duration_ms INT NOT NULL DEFAULT 0,
    error_message NVARCHAR(1000) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_scan_history PRIMARY KEY CLUSTERED (id),
    CONSTRAINT fk_scan_project FOREIGN KEY (project_id) 
        REFERENCES dbo.projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_scan_user FOREIGN KEY (scanned_by) 
        REFERENCES dbo.users(id),
    CONSTRAINT chk_scan_status CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'))
);

-- =====================================================================
-- 10. RISK_ASSESSMENTS TABLE
-- Computed graph risk score, depth metrics, and single points of failure
-- =====================================================================
CREATE TABLE dbo.risk_assessments (
    id NVARCHAR(64) NOT NULL,
    project_id NVARCHAR(64) NOT NULL,
    scan_id NVARCHAR(64) NULL,
    overall_score FLOAT NOT NULL DEFAULT 0.0, -- Range: 0.0 - 100.0
    risk_level NVARCHAR(50) NOT NULL DEFAULT 'LOW', -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    max_depth INT NOT NULL DEFAULT 1,
    critical_deps_count INT NOT NULL DEFAULT 0,
    spof_count INT NOT NULL DEFAULT 0, -- Single Points of Failure
    direct_vulnerabilities INT NOT NULL DEFAULT 0,
    transitive_vulnerabilities INT NOT NULL DEFAULT 0,
    details_json NVARCHAR(MAX) NULL, -- Semi-structured breakdown of risk factors
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_risk_assessments PRIMARY KEY CLUSTERED (id),
    CONSTRAINT fk_risk_project FOREIGN KEY (project_id) 
        REFERENCES dbo.projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_risk_scan FOREIGN KEY (scan_id) 
        REFERENCES dbo.scan_history(id),
    CONSTRAINT chk_risk_level CHECK (risk_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'))
);

-- =====================================================================
-- 11. ACTIVITY_LOGS TABLE
-- Security audit trail recording system actions for Cloud Compliance
-- =====================================================================
CREATE TABLE dbo.activity_logs (
    id NVARCHAR(64) NOT NULL,
    organization_id NVARCHAR(64) NULL,
    user_id NVARCHAR(64) NULL,
    action NVARCHAR(100) NOT NULL, -- 'AUTH_LOGIN', 'PROJECT_CREATE', 'MANIFEST_UPLOAD', 'VULN_SCAN', etc.
    entity_type NVARCHAR(50) NOT NULL, -- 'USER', 'PROJECT', 'SCAN', 'REPORT'
    entity_id NVARCHAR(64) NULL,
    details NVARCHAR(1000) NULL,
    ip_address NVARCHAR(50) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT pk_activity_logs PRIMARY KEY CLUSTERED (id),
    CONSTRAINT fk_activity_org FOREIGN KEY (organization_id) 
        REFERENCES dbo.organizations(id),
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) 
        REFERENCES dbo.users(id)
);

-- =====================================================================
-- INDEXES FOR FREQUENTLY SEARCHED / JOINED COLUMNS
-- =====================================================================
CREATE NONCLUSTERED INDEX ix_dependencies_project ON dbo.dependencies(project_id);
CREATE NONCLUSTERED INDEX ix_dependencies_package ON dbo.dependencies(package_id);
CREATE NONCLUSTERED INDEX ix_packages_name ON dbo.packages(name);
CREATE NONCLUSTERED INDEX ix_vulnerabilities_pkg ON dbo.vulnerabilities(affected_package);
CREATE NONCLUSTERED INDEX ix_vulnerabilities_osv ON dbo.vulnerabilities(osv_id);
CREATE NONCLUSTERED INDEX ix_pkg_vuln_package ON dbo.package_vulnerabilities(package_id);
CREATE NONCLUSTERED INDEX ix_pkg_vuln_vuln ON dbo.package_vulnerabilities(vulnerability_id);
CREATE NONCLUSTERED INDEX ix_scan_project ON dbo.scan_history(project_id);
CREATE NONCLUSTERED INDEX ix_risk_project ON dbo.risk_assessments(project_id);
CREATE NONCLUSTERED INDEX ix_activity_org ON dbo.activity_logs(organization_id);
CREATE NONCLUSTERED INDEX ix_activity_user ON dbo.activity_logs(user_id);

-- =====================================================================
-- DATABASE VIEW: v_project_risk_summary
-- Aggregates project information with latest risk score and vulnerability metrics
-- =====================================================================
GO
CREATE VIEW dbo.v_project_risk_summary AS
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
FROM dbo.projects p
LEFT JOIN (
    SELECT project_id, overall_score, risk_level, max_depth, spof_count,
           ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at DESC) as rn
    FROM dbo.risk_assessments
) r ON p.id = r.project_id AND r.rn = 1
LEFT JOIN (
    SELECT project_id, vulnerable_packages_count, critical_count, high_count, medium_count, low_count, created_at,
           ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at DESC) as rn
    FROM dbo.scan_history
    WHERE status = 'COMPLETED'
) s ON p.id = s.project_id AND s.rn = 1;
GO

-- =====================================================================
-- DATABASE VIEW: v_vulnerable_dependencies
-- Joins projects, dependencies, packages, and matched vulnerabilities
-- =====================================================================
GO
CREATE VIEW dbo.v_vulnerable_dependencies AS
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
FROM dbo.dependencies d
JOIN dbo.projects p ON d.project_id = p.id
JOIN dbo.packages pkg ON d.package_id = pkg.id
JOIN dbo.package_vulnerabilities pv ON pkg.id = pv.package_id AND d.resolved_version = pv.matched_version
JOIN dbo.vulnerabilities v ON pv.vulnerability_id = v.id;
GO

-- =====================================================================
-- STORED PROCEDURE: sp_calculate_project_risk_metrics
-- Demonstrates stored procedure implementation for Azure SQL
-- =====================================================================
GO
CREATE PROCEDURE dbo.sp_calculate_project_risk_metrics
    @ProjectId NVARCHAR(64)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @DirectCount INT = 0;
    DECLARE @TransitiveCount INT = 0;
    DECLARE @MaxDepth INT = 1;
    DECLARE @CriticalVulns INT = 0;
    DECLARE @HighVulns INT = 0;
    DECLARE @MediumVulns INT = 0;
    DECLARE @LowVulns INT = 0;

    -- Calculate dependency counts and max depth
    SELECT 
        @DirectCount = COUNT(CASE WHEN is_direct = 1 THEN 1 END),
        @TransitiveCount = COUNT(CASE WHEN is_direct = 0 THEN 1 END),
        @MaxDepth = COALESCE(MAX(depth), 1)
    FROM dbo.dependencies
    WHERE project_id = @ProjectId;

    -- Return calculated summary result
    SELECT 
        @ProjectId AS project_id,
        @DirectCount AS direct_dependencies_count,
        @TransitiveCount AS transitive_dependencies_count,
        @MaxDepth AS max_tree_depth;
END;
GO
