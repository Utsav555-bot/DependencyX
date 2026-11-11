# DependencyX — Entity Relationship Diagram & RDBMS Normalization Guide

## 1. Relational Database Architecture Overview

DependencyX implements an enterprise-grade Relational Database Management System (RDBMS) schema designed in **Third Normal Form (3NF)** to ensure zero data redundancy, transactional integrity, and compliance with Microsoft Azure SQL Database standards.

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ ORGANIZATION_MEMBERS : has
    USERS ||--o{ ORGANIZATION_MEMBERS : belongs_to
    ORGANIZATIONS ||--o{ PROJECTS : owns
    USERS ||--o{ PROJECTS : creates
    PROJECTS ||--o{ DEPENDENCIES : contains
    PACKAGES ||--o{ DEPENDENCIES : referenced_by
    PACKAGES ||--o{ DEPENDENCIES : parent_of
    PACKAGES ||--o{ PACKAGE_VULNERABILITIES : has
    VULNERABILITIES ||--o{ PACKAGE_VULNERABILITIES : maps_to
    PROJECTS ||--o{ SCAN_HISTORY : audited_in
    USERS ||--o{ SCAN_HISTORY : initiated_by
    PROJECTS ||--o{ RISK_ASSESSMENTS : assessed_by
    SCAN_HISTORY ||--o| RISK_ASSESSMENTS : triggers
    ORGANIZATIONS ||--o{ ACTIVITY_LOGS : scopes
    USERS ||--o{ ACTIVITY_LOGS : records

    ORGANIZATIONS {
        string id PK
        string name
        string slug UK
        string description
        datetime created_at
    }

    USERS {
        string id PK
        string email UK
        string hashed_password
        string full_name
        string role "admin | developer"
        boolean is_active
        datetime created_at
    }

    ORGANIZATION_MEMBERS {
        string id PK
        string organization_id FK
        string user_id FK
        string role "admin | developer"
        datetime created_at
    }

    PROJECTS {
        string id PK
        string organization_id FK
        string name
        string description
        string ecosystem "npm"
        string repository_url
        string manifest_blob_path
        string created_by FK
        datetime created_at
    }

    PACKAGES {
        string id PK
        string name
        string ecosystem "npm"
        string latest_version
        string description
        string license
        datetime created_at
    }

    DEPENDENCIES {
        string id PK
        string project_id FK
        string package_id FK
        string version_spec
        string resolved_version
        boolean is_direct
        string dependency_type
        int depth
        string parent_package_id FK
        datetime created_at
    }

    VULNERABILITIES {
        string id PK
        string osv_id UK
        string cve_id
        string ghsa_id
        string summary
        string severity "CRITICAL | HIGH | MEDIUM | LOW"
        float cvss_score
        string affected_ecosystem
        string affected_package
        string affected_range
        string fixed_version
        datetime published_at
    }

    PACKAGE_VULNERABILITIES {
        string id PK
        string package_id FK
        string vulnerability_id FK
        string matched_version
        datetime detected_at
    }

    SCAN_HISTORY {
        string id PK
        string project_id FK
        string scanned_by FK
        string status "PENDING | IN_PROGRESS | COMPLETED | FAILED"
        int total_packages
        int vulnerable_packages_count
        int critical_count
        int high_count
        int medium_count
        int low_count
        int duration_ms
        datetime created_at
    }

    RISK_ASSESSMENTS {
        string id PK
        string project_id FK
        string scan_id FK
        float overall_score
        string risk_level "CRITICAL | HIGH | MEDIUM | LOW"
        int max_depth
        int critical_deps_count
        int spof_count
        int direct_vulnerabilities
        int transitive_vulnerabilities
        string details_json
        datetime created_at
    }

    ACTIVITY_LOGS {
        string id PK
        string organization_id FK
        string user_id FK
        string action
        string entity_type
        string entity_id
        string details
        string ip_address
        datetime created_at
    }
```

---

## 2. Normalization Verification (1NF to 3NF)

### First Normal Form (1NF) Compliance
- **Atomic Values**: Every attribute in every table stores atomic, non-decomposable values. No repeating groups or comma-separated lists exist for dependencies or vulnerabilities.
- **Unique Identification**: Every table possesses a clear Primary Key (`id`), enforcing unique row identification.
- **Predictable Types**: Well-defined column types (e.g., `NVARCHAR`, `DATETIME2`, `INT`, `FLOAT`, `BIT`).

### Second Normal Form (2NF) Compliance
- Meets all criteria of 1NF.
- **No Partial Dependencies**: In tables with composite business keys (e.g. `organization_members(organization_id, user_id)` or `package_vulnerabilities(package_id, vulnerability_id, matched_version)`), every non-key attribute is fully functionally dependent on the primary key, eliminating partial functional dependencies.

### Third Normal Form (3NF) Compliance
- Meets all criteria of 2NF.
- **No Transitive Dependencies**: Non-prime attributes are non-transitively dependent on primary keys ($X \to Y \to Z$ is eliminated).
  - Package metadata (e.g. `description`, `license`) is stored once in `PACKAGES`, not duplicated across each `DEPENDENCY` row.
  - Vulnerability details (e.g. `cvss_score`, `severity`, `summary`) are stored in `VULNERABILITIES`, mapped to packages through the associative junction entity `PACKAGE_VULNERABILITIES`.
  - Organization data is separate from `USERS` and mapped via `ORGANIZATION_MEMBERS`, ensuring multi-tenancy and data isolation without duplicating organization details.

---

## 3. RDBMS Advanced Features Implemented

1. **Database Views**:
   - `dbo.v_project_risk_summary`: Combines projects, latest scan statistics, and evaluated risk score for instant dashboard queries without multi-query overhead.
   - `dbo.v_vulnerable_dependencies`: Pre-joined view linking projects, packages, dependencies, and OSV security alerts.
2. **Stored Procedures**:
   - `dbo.sp_calculate_project_risk_metrics`: Computes direct vs. transitive counts, max depth, and vulnerability counts server-side inside Azure SQL.
3. **Transactions (ACID)**:
   - Manifest upload and dependency tree extraction run within an atomic transaction. If parsing fails midway, all changes are rolled back.
4. **Targeted Indexes**:
   - B-tree non-clustered indexes on `dependencies(project_id)`, `dependencies(package_id)`, `packages(name)`, `vulnerabilities(osv_id)`, and `scan_history(project_id)`.
