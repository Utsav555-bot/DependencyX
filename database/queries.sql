-- =====================================================================
-- DependencyX - Software Dependency Risk Map
-- SQL Query File (RDBMS Demonstration Queries)
-- =====================================================================

-- ---------------------------------------------------------------------
-- QUERY 1: Multi-Table JOIN - Fetch Complete Project Dependency Inventory
-- Combines Projects, Dependencies, and Packages
-- ---------------------------------------------------------------------
SELECT 
    p.id AS project_id,
    p.name AS project_name,
    p.ecosystem,
    pkg.name AS package_name,
    d.resolved_version,
    d.is_direct,
    d.depth,
    parent.name AS parent_package_name
FROM dbo.projects p
INNER JOIN dbo.dependencies d ON p.id = d.project_id
INNER JOIN dbo.packages pkg ON d.package_id = pkg.id
LEFT JOIN dbo.packages parent ON d.parent_package_id = parent.id
ORDER BY p.name, d.depth, pkg.name;

-- ---------------------------------------------------------------------
-- QUERY 2: Vulnerability Impact JOIN - List all Vulnerable Dependencies with Severity
-- ---------------------------------------------------------------------
SELECT 
    p.name AS project_name,
    pkg.name AS package_name,
    d.resolved_version,
    d.depth,
    CASE WHEN d.is_direct = 1 THEN 'Direct' ELSE 'Transitive' END AS dependency_nature,
    v.osv_id,
    v.cve_id,
    v.severity,
    v.cvss_score,
    v.summary,
    v.fixed_version
FROM dbo.dependencies d
INNER JOIN dbo.projects p ON d.project_id = p.id
INNER JOIN dbo.packages pkg ON d.package_id = pkg.id
INNER JOIN dbo.package_vulnerabilities pv ON pkg.id = pv.package_id AND d.resolved_version = pv.matched_version
INNER JOIN dbo.vulnerabilities v ON pv.vulnerability_id = v.id
ORDER BY 
    CASE v.severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        WHEN 'LOW' THEN 4 
    END;

-- ---------------------------------------------------------------------
-- QUERY 3: Reverse Vulnerability Propagation Traversal
-- Given a vulnerable package (e.g., 'lodash'), identify every project
-- and whether the impact is direct or transitive.
-- ---------------------------------------------------------------------
SELECT 
    pkg.name AS vulnerable_package,
    d.resolved_version,
    p.id AS affected_project_id,
    p.name AS affected_project_name,
    d.depth AS dependency_depth,
    d.is_direct AS is_directly_affected,
    v.osv_id,
    v.severity,
    v.summary
FROM dbo.packages pkg
INNER JOIN dbo.package_vulnerabilities pv ON pkg.id = pv.package_id
INNER JOIN dbo.vulnerabilities v ON pv.vulnerability_id = v.id
INNER JOIN dbo.dependencies d ON pkg.id = d.package_id AND d.resolved_version = pv.matched_version
INNER JOIN dbo.projects p ON d.project_id = p.id
WHERE pkg.name = 'lodash'
ORDER BY d.depth ASC;

-- ---------------------------------------------------------------------
-- QUERY 4: Aggregation & GROUP BY - Organization-Wide Security Metrics
-- ---------------------------------------------------------------------
SELECT 
    o.name AS organization_name,
    COUNT(DISTINCT p.id) AS total_projects,
    COUNT(DISTINCT d.package_id) AS total_unique_packages,
    COUNT(DISTINCT CASE WHEN pv.vulnerability_id IS NOT NULL THEN d.package_id END) AS vulnerable_packages_count,
    COUNT(DISTINCT v.id) AS total_distinct_vulnerabilities,
    SUM(CASE WHEN v.severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_vuln_count,
    SUM(CASE WHEN v.severity = 'HIGH' THEN 1 ELSE 0 END) AS high_vuln_count,
    AVG(COALESCE(r.overall_score, 0.0)) AS avg_organization_risk_score
FROM dbo.organizations o
LEFT JOIN dbo.projects p ON o.id = p.organization_id
LEFT JOIN dbo.dependencies d ON p.id = d.project_id
LEFT JOIN dbo.package_vulnerabilities pv ON d.package_id = pv.package_id AND d.resolved_version = pv.matched_version
LEFT JOIN dbo.vulnerabilities v ON pv.vulnerability_id = v.id
LEFT JOIN dbo.risk_assessments r ON p.id = r.project_id
GROUP BY o.id, o.name;

-- ---------------------------------------------------------------------
-- QUERY 5: Querying Database View: v_project_risk_summary
-- ---------------------------------------------------------------------
SELECT 
    project_id,
    project_name,
    ecosystem,
    latest_risk_score,
    latest_risk_level,
    max_dependency_depth,
    vulnerable_packages_count,
    critical_vuln_count,
    high_vuln_count,
    last_scan_date
FROM dbo.v_project_risk_summary
ORDER BY latest_risk_score DESC;

-- ---------------------------------------------------------------------
-- QUERY 6: Calling Stored Procedure: sp_calculate_project_risk_metrics
-- ---------------------------------------------------------------------
EXEC dbo.sp_calculate_project_risk_metrics @ProjectId = 'prj_ecomm_01';

-- ---------------------------------------------------------------------
-- QUERY 7: Transaction Demonstration - Atomic Project & Scan Ingestion
-- Demonstrates ACID properties (Atomicity, Consistency, Isolation, Durability)
-- ---------------------------------------------------------------------
BEGIN TRANSACTION;

BEGIN TRY
    -- 1. Insert Project
    INSERT INTO dbo.projects (id, organization_id, name, description, ecosystem, created_by)
    VALUES ('prj_trans_demo', 'org_acme_01', 'Transaction Demo App', 'ACID transaction test project', 'npm', 'usr_admin_01');

    -- 2. Insert Dependency
    INSERT INTO dbo.dependencies (id, project_id, package_id, version_spec, resolved_version, is_direct, depth)
    VALUES ('dep_trans_01', 'prj_trans_demo', 'pkg_react', '^18.2.0', '18.2.0', 1, 1);

    -- 3. Log Activity
    INSERT INTO dbo.activity_logs (id, organization_id, user_id, action, entity_type, entity_id, details)
    VALUES ('act_trans_01', 'org_acme_01', 'usr_admin_01', 'PROJECT_CREATE', 'PROJECT', 'prj_trans_demo', 'Created within atomic transaction');

    COMMIT TRANSACTION;
    PRINT 'Transaction committed successfully.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    PRINT 'Transaction rolled back due to error: ' + ERROR_MESSAGE();
END CATCH;
