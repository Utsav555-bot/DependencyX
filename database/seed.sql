-- =====================================================================
-- DependencyX - Software Dependency Risk Map
-- Seed Data Script
-- Populates 11 tables with realistic sample data for demo and testing
-- =====================================================================

-- 1. Insert Initial Users
-- Password for all seed users is: Password123!
-- (Bcrypt hash: $2b$12$e68BqH10t0JzCkW6xX1vIe48yB10E2oIgl7kL0d4nO2s7r5vU8/G2)
INSERT INTO dbo.users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
VALUES 
('usr_admin_01', 'admin@dependencyx.io', '$2b$12$e68BqH10t0JzCkW6xX1vIe48yB10E2oIgl7kL0d4nO2s7r5vU8/G2', 'Security Administrator', 'admin', 1, SYSUTCDATETIME(), SYSUTCDATETIME()),
('usr_dev_01', 'developer@dependencyx.io', '$2b$12$e68BqH10t0JzCkW6xX1vIe48yB10E2oIgl7kL0d4nO2s7r5vU8/G2', 'Lead Fullstack Dev', 'developer', 1, SYSUTCDATETIME(), SYSUTCDATETIME());

-- 2. Insert Organizations
INSERT INTO dbo.organizations (id, name, slug, description, created_at, updated_at)
VALUES 
('org_acme_01', 'Acme CyberSec Global', 'acme-cybersec', 'Enterprise application suite security monitoring', SYSUTCDATETIME(), SYSUTCDATETIME());

-- 3. Insert Organization Members
INSERT INTO dbo.organization_members (id, organization_id, user_id, role, created_at)
VALUES 
('mem_01', 'org_acme_01', 'usr_admin_01', 'admin', SYSUTCDATETIME()),
('mem_02', 'org_acme_01', 'usr_dev_01', 'developer', SYSUTCDATETIME());

-- 4. Insert Projects
INSERT INTO dbo.projects (id, organization_id, name, description, ecosystem, repository_url, manifest_blob_path, created_by, created_at, updated_at)
VALUES 
('prj_ecomm_01', 'org_acme_01', 'Storefront Web App', 'Customer facing web shop with product search and checkout', 'npm', 'https://github.com/acme/storefront-web', 'manifests/prj_ecomm_01/package-lock.json', 'usr_admin_01', SYSUTCDATETIME(), SYSUTCDATETIME()),
('prj_pay_02', 'org_acme_01', 'Payment Gateway Integration', 'PCI-DSS compliant payment integration microservice', 'npm', 'https://github.com/acme/payment-gateway', 'manifests/prj_pay_02/package-lock.json', 'usr_dev_01', SYSUTCDATETIME(), SYSUTCDATETIME()),
('prj_notif_03', 'org_acme_01', 'Cloud Notification Engine', 'Event-driven email, SMS and push dispatch worker', 'npm', 'https://github.com/acme/notification-engine', 'manifests/prj_notif_03/package-lock.json', 'usr_dev_01', SYSUTCDATETIME(), SYSUTCDATETIME());

-- 5. Insert Packages
INSERT INTO dbo.packages (id, name, ecosystem, latest_version, description, license, created_at, updated_at)
VALUES 
('pkg_lodash', 'lodash', 'npm', '4.17.21', 'Lodash modular utilities.', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_axios', 'axios', 'npm', '1.6.8', 'Promise based HTTP client for the browser and node.js', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_express', 'express', 'npm', '4.19.2', 'Fast, unopinionated, minimalist web framework', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_jwt', 'jsonwebtoken', 'npm', '9.0.2', 'JSON Web Token implementation (symmetric and asymmetric)', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_react', 'react', 'npm', '18.2.0', 'React is a JavaScript library for building user interfaces.', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_cookie', 'cookie', 'npm', '0.7.0', 'HTTP server cookie parsing and serialization', 'MIT', SYSUTCDATETIME(), SYSUTCDATETIME()),
('pkg_semver', 'semver', 'npm', '7.6.0', 'The semantic versioner for npm', 'ISC', SYSUTCDATETIME(), SYSUTCDATETIME());

-- 6. Insert Dependencies (Connecting Projects to Packages)
INSERT INTO dbo.dependencies (id, project_id, package_id, version_spec, resolved_version, is_direct, dependency_type, depth, parent_package_id, created_at)
VALUES 
-- Storefront Web App dependencies
('dep_01', 'prj_ecomm_01', 'pkg_react', '^18.2.0', '18.2.0', 1, 'dependencies', 1, NULL, SYSUTCDATETIME()),
('dep_02', 'prj_ecomm_01', 'pkg_axios', '^0.21.1', '0.21.1', 1, 'dependencies', 1, NULL, SYSUTCDATETIME()),
('dep_03', 'prj_ecomm_01', 'pkg_lodash', '^4.17.15', '4.17.15', 0, 'dependencies', 2, 'pkg_axios', SYSUTCDATETIME()),
-- Payment Gateway dependencies
('dep_04', 'prj_pay_02', 'pkg_express', '^4.16.0', '4.16.0', 1, 'dependencies', 1, NULL, SYSUTCDATETIME()),
('dep_05', 'prj_pay_02', 'pkg_jwt', '^8.5.1', '8.5.1', 1, 'dependencies', 1, NULL, SYSUTCDATETIME()),
('dep_06', 'prj_pay_02', 'pkg_cookie', '^0.3.1', '0.3.1', 0, 'dependencies', 2, 'pkg_express', SYSUTCDATETIME()),
('dep_07', 'prj_pay_02', 'pkg_semver', '^5.7.1', '5.7.1', 0, 'dependencies', 2, 'pkg_jwt', SYSUTCDATETIME()),
-- Notification Engine dependencies
('dep_08', 'prj_notif_03', 'pkg_axios', '^1.6.8', '1.6.8', 1, 'dependencies', 1, NULL, SYSUTCDATETIME()),
('dep_09', 'prj_notif_03', 'pkg_lodash', '^4.17.21', '4.17.21', 1, 'dependencies', 1, NULL, SYSUTCDATETIME());

-- 7. Insert Known Vulnerabilities (OSV/CVE)
INSERT INTO dbo.vulnerabilities (id, osv_id, cve_id, ghsa_id, summary, details, severity, cvss_score, affected_ecosystem, affected_package, affected_range, fixed_version, published_at, retrieved_at)
VALUES 
('vuln_01', 'GHSA-35jh-r3h4-6jhm', 'CVE-2020-8203', 'GHSA-35jh-r3h4-6jhm', 'Prototype Pollution in lodash', 'Prototype pollution vulnerability in lodash before 4.17.19 via zipObjectDeep function.', 'HIGH', 7.4, 'npm', 'lodash', '<4.17.19', '4.17.19', '2020-07-15T00:00:00Z', SYSUTCDATETIME()),
('vuln_02', 'GHSA-42xw-2xvc-cxqx', 'CVE-2021-23343', 'GHSA-42xw-2xvc-cxqx', 'ReDoS in path-to-regexp / axios dependency', 'Regular expression denial of service in axios param serializer before 0.21.2.', 'MEDIUM', 5.3, 'npm', 'axios', '<0.21.2', '0.21.2', '2021-08-31T00:00:00Z', SYSUTCDATETIME()),
('vuln_03', 'GHSA-hjrf-2m68-5959', 'CVE-2022-23529', 'GHSA-hjrf-2m68-5959', 'Remote Code Execution in jsonwebtoken verify()', 'Insecure key retrieval allows remote code execution when verifying forged tokens in jsonwebtoken < 9.0.0.', 'CRITICAL', 9.8, 'npm', 'jsonwebtoken', '<9.0.0', '9.0.0', '2022-12-21T00:00:00Z', SYSUTCDATETIME()),
('vuln_04', 'GHSA-pxg6-pf52-xh8x', 'CVE-2024-47764', 'GHSA-pxg6-pf52-xh8x', 'cookie allows out-of-bounds character parsing', 'Cookie parser in cookie prior to 0.7.0 can trigger out of bounds read on corrupted headers.', 'LOW', 3.7, 'npm', 'cookie', '<0.7.0', '0.7.0', '2024-10-08T00:00:00Z', SYSUTCDATETIME());

-- 8. Map Package Vulnerabilities
INSERT INTO dbo.package_vulnerabilities (id, package_id, vulnerability_id, matched_version, detected_at)
VALUES 
('pv_01', 'pkg_lodash', 'vuln_01', '4.17.15', SYSUTCDATETIME()),
('pv_02', 'pkg_axios', 'vuln_02', '0.21.1', SYSUTCDATETIME()),
('pv_03', 'pkg_jwt', 'vuln_03', '8.5.1', SYSUTCDATETIME()),
('pv_04', 'pkg_cookie', 'vuln_04', '0.3.1', SYSUTCDATETIME());

-- 9. Insert Scan History Records
INSERT INTO dbo.scan_history (id, project_id, scanned_by, status, total_packages, vulnerable_packages_count, critical_count, high_count, medium_count, low_count, duration_ms, error_message, created_at)
VALUES 
('scan_01', 'prj_ecomm_01', 'usr_admin_01', 'COMPLETED', 3, 2, 0, 1, 1, 0, 1420, NULL, SYSUTCDATETIME()),
('scan_02', 'prj_pay_02', 'usr_dev_01', 'COMPLETED', 4, 2, 1, 0, 0, 1, 1850, NULL, SYSUTCDATETIME()),
('scan_03', 'prj_notif_03', 'usr_dev_01', 'COMPLETED', 2, 0, 0, 0, 0, 0, 680, NULL, SYSUTCDATETIME());

-- 10. Insert Risk Assessments
INSERT INTO dbo.risk_assessments (id, project_id, scan_id, overall_score, risk_level, max_depth, critical_deps_count, spof_count, direct_vulnerabilities, transitive_vulnerabilities, details_json, created_at)
VALUES 
('risk_01', 'prj_ecomm_01', 'scan_01', 68.5, 'HIGH', 2, 1, 1, 1, 1, '{"propagation_depth": 2, "factors": ["Transitive high severity vuln in lodash", "Direct medium vuln in axios"]}', SYSUTCDATETIME()),
('risk_02', 'prj_pay_02', 'scan_02', 92.0, 'CRITICAL', 2, 2, 1, 1, 1, '{"propagation_depth": 2, "factors": ["Critical CVE-2022-23529 RCE in direct jwt dependency", "Transitive cookie vuln"]}', SYSUTCDATETIME()),
('risk_03', 'prj_notif_03', 'scan_03', 12.0, 'LOW', 1, 0, 0, 0, 0, '{"propagation_depth": 1, "factors": ["All dependencies resolved to secure patched versions"]}', SYSUTCDATETIME());

-- 11. Insert Activity Logs
INSERT INTO dbo.activity_logs (id, organization_id, user_id, action, entity_type, entity_id, details, ip_address, created_at)
VALUES 
('act_01', 'org_acme_01', 'usr_admin_01', 'AUTH_LOGIN', 'USER', 'usr_admin_01', 'User authenticated via JWT bearer token', '127.0.0.1', SYSUTCDATETIME()),
('act_02', 'org_acme_01', 'usr_admin_01', 'PROJECT_CREATE', 'PROJECT', 'prj_ecomm_01', 'Created project Storefront Web App', '127.0.0.1', SYSUTCDATETIME()),
('act_03', 'org_acme_01', 'usr_admin_01', 'MANIFEST_UPLOAD', 'PROJECT', 'prj_ecomm_01', 'Uploaded package-lock.json v2 (3 packages)', '127.0.0.1', SYSUTCDATETIME()),
('act_04', 'org_acme_01', 'usr_admin_01', 'VULN_SCAN', 'SCAN', 'scan_01', 'Completed OSV vulnerability scan: 2 vulnerabilities found', '127.0.0.1', SYSUTCDATETIME()),
('act_05', 'org_acme_01', 'usr_dev_01', 'PROJECT_CREATE', 'PROJECT', 'prj_pay_02', 'Created project Payment Gateway Integration', '127.0.0.1', SYSUTCDATETIME()),
('act_06', 'org_acme_01', 'usr_dev_01', 'VULN_SCAN', 'SCAN', 'scan_02', 'Completed OSV scan: 1 Critical, 1 Low vulnerability', '127.0.0.1', SYSUTCDATETIME());
