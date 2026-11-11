export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'developer';
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id?: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  ecosystem: string;
  repository_url?: string;
  manifest_blob_path?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  total_dependencies: number;
  vulnerable_packages_count: number;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface DependencyItem {
  id: string;
  package_name: string;
  resolved_version: string;
  is_direct: boolean;
  dependency_type: string;
  depth: number;
  parent_package_name?: string;
  has_vulnerability?: boolean;
  highest_severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
}

export interface VulnerabilityItem {
  id: string;
  osv_id: string;
  cve_id?: string;
  ghsa_id?: string;
  summary?: string;
  details?: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  cvss_score?: number;
  affected_package: string;
  affected_range?: string;
  fixed_version?: string;
  published_at?: string;
}

export interface GraphNodeData {
  id: string;
  label: string;
  version: string;
  node_type?: 'project_root' | 'package';
  is_direct?: boolean;
  depth?: number;
  is_vulnerable?: boolean;
  highest_severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  vulnerabilities?: VulnerabilityItem[];
  in_degree?: number;
  out_degree?: number;
  betweenness?: number;
}

export interface GraphResponse {
  root_node_id: string;
  nodes: {
    id: string;
    type: string;
    position: { x: number; y: number };
    data: GraphNodeData;
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
    animated?: boolean;
    style?: any;
    data?: any;
  }[];
  summary: {
    total_nodes: number;
    total_edges: number;
    max_depth: number;
    direct_count: number;
    transitive_count: number;
    circular_dependencies: string[];
    has_circular: boolean;
    depth_distribution?: Record<string, number>;
  };
}

export interface RiskDetails {
  project_id: string;
  project_name: string;
  overall_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  max_depth: number;
  critical_deps_count: number;
  spof_count: number;
  direct_vulnerabilities: number;
  transitive_vulnerabilities: number;
  vulnerable_packages: any[];
  critical_dependencies: any[];
  single_points_of_failure: any[];
  breakdown: Record<string, any>;
}

export interface DashboardMetrics {
  total_projects: number;
  total_unique_packages: number;
  total_dependencies: number;
  vulnerable_packages: number;
  critical_vulnerabilities: number;
  high_risk_projects: number;
  affected_projects: number;
  overall_org_risk_score: number;
}

export interface DashboardAnalytics {
  metrics: DashboardMetrics;
  severity_distribution: { severity: string; count: number }[];
  top_vulnerable_packages: {
    package_name: string;
    vulnerabilities_count: number;
    highest_severity: string;
    cve_ids: string[];
  }[];
  project_risk_comparison: {
    project_id: string;
    project_name: string;
    risk_score: number;
    risk_level: string;
    vulnerabilities: number;
    spof_count: number;
  }[];
  depth_distribution: { depth: number; count: number }[];
  recent_activity: any[];
  latest_alerts: any[];
}
