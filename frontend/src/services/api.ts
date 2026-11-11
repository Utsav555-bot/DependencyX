import {
  AuthResponse,
  Project,
  DependencyItem,
  VulnerabilityItem,
  GraphResponse,
  RiskDetails,
  DashboardAnalytics,
  User
} from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

class ApiService {
  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('dependencyx_token');
    }
    return null;
  }

  public setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('dependencyx_token', token);
    }
  }

  public removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('dependencyx_token');
      localStorage.removeItem('dependencyx_user');
    }
  }

  public getStoredUser(): any {
    if (typeof window !== 'undefined') {
      const data = localStorage.getItem('dependencyx_user');
      if (data) {
        try {
          return JSON.parse(data);
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  public setStoredUser(user: any): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('dependencyx_user', JSON.stringify(user));
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.removeToken();
      // Only redirect or notify if not on initial public pages
      throw new Error('Session expired or unauthorized. Please log in.');
    }

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errorData = await res.json();
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch {
        errorMsg = await res.text();
      }
      throw new Error(errorMsg);
    }

    if (res.status === 204) {
      return null as any;
    }

    return res.json();
  }

  // Auth
  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setToken(data.access_token);
    this.setStoredUser(data);
    return data;
  }

  async register(payload: any): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setToken(data.access_token);
    this.setStoredUser(data);
    return data;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/projects');
  }

  async getProject(id: string): Promise<Project> {
    return this.request<Project>(`/projects/${id}`);
  }

  async createProject(payload: { name: string; description?: string; ecosystem?: string; repository_url?: string }): Promise<Project> {
    return this.request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async deleteProject(id: string): Promise<void> {
    return this.request<void>(`/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // Upload Manifest
  async uploadManifest(projectId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<any>(`/projects/${projectId}/upload`, {
      method: 'POST',
      body: formData,
    });
  }

  // Dependencies & Graph
  async getDependencies(projectId: string): Promise<DependencyItem[]> {
    return this.request<DependencyItem[]>(`/projects/${projectId}/dependencies`);
  }

  async getGraph(projectId: string): Promise<GraphResponse> {
    return this.request<GraphResponse>(`/projects/${projectId}/graph`);
  }

  // Vulnerabilities
  async triggerScan(projectId: string): Promise<any> {
    return this.request<any>(`/projects/${projectId}/scan`, {
      method: 'POST',
    });
  }

  async getProjectVulnerabilities(projectId: string): Promise<VulnerabilityItem[]> {
    return this.request<VulnerabilityItem[]>(`/projects/${projectId}/vulnerabilities`);
  }

  async getAllVulnerabilities(): Promise<VulnerabilityItem[]> {
    return this.request<VulnerabilityItem[]>('/vulnerabilities');
  }

  // Risk
  async getProjectRisk(projectId: string): Promise<RiskDetails> {
    return this.request<RiskDetails>(`/projects/${projectId}/risk`);
  }

  async getOrgRisk(): Promise<any> {
    return this.request<any>('/risk/organization');
  }

  async getCriticalDependencies(): Promise<any[]> {
    return this.request<any[]>('/risk/critical-dependencies');
  }

  // Analytics
  async getDashboardAnalytics(): Promise<DashboardAnalytics> {
    return this.request<DashboardAnalytics>('/analytics/dashboard');
  }

  // Reports
  getExportUrl(projectId: string, format: 'csv' | 'html' = 'csv'): string {
    const token = this.getToken();
    return `${API_BASE}/reports/${projectId}/export?format=${format}`;
  }

  async downloadReport(projectId: string, format: 'csv' | 'html' = 'csv'): Promise<Blob> {
    const token = this.getToken();
    const res = await fetch(`${API_BASE}/reports/${projectId}/export?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error('Failed to download report');
    return res.blob();
  }

  // Activity Logs
  async getActivityLogs(): Promise<any[]> {
    return this.request<any[]>('/activity');
  }
}

export const api = new ApiService();
