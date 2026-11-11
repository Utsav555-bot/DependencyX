'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ShieldAlert,
  Flame,
  Layers,
  FolderGit2,
  AlertTriangle,
  ArrowRight,
  Download,
  Activity,
  CheckCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { DashboardAnalytics } from '../types';
import { RiskGauge } from '../components/RiskGauge';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#EF4444',
  HIGH: '#F97316',
  MEDIUM: '#F59E0B',
  LOW: '#10B981',
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboardAnalytics();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent"></div>
          <p className="text-xs text-slate-400">Loading DependencyX Security Intelligence...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-rose-400 mb-2" />
        <h3 className="text-sm font-bold text-rose-300">Database Connection Required</h3>
        <p className="text-xs text-slate-400 mt-1">{error || 'Could not fetch dashboard metrics.'}</p>
        <button
          onClick={loadData}
          className="mt-4 rounded-lg bg-rose-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-rose-500 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { metrics, severity_distribution, top_vulnerable_packages, project_risk_comparison, depth_distribution, recent_activity } = data;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            Security Intelligence Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time RDBMS-driven dependency risk mapping &bull; Multi-project vulnerability propagation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/graph"
            className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-600/20 hover:bg-cyan-500 transition"
          >
            <span>Explore Graph</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* 8 Primary Metrics Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-4">
        {/* Metric 1 */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Projects</span>
            <FolderGit2 className="h-4 w-4 text-cyan-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-white">{metrics.total_projects}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Monitored in Organization</p>
        </div>

        {/* Metric 2 */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Unique Packages</span>
            <Layers className="h-4 w-4 text-cyan-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-white">{metrics.total_unique_packages}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">{metrics.total_dependencies} dependency edges</p>
        </div>

        {/* Metric 3 */}
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-4 shadow-lg backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-rose-300 uppercase tracking-wider">Vulnerable Packages</span>
            <ShieldAlert className="h-4 w-4 text-rose-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-rose-400">{metrics.vulnerable_packages}</p>
          <p className="text-[10px] text-rose-300/70 mt-0.5">{metrics.critical_vulnerabilities} Critical CVEs</p>
        </div>

        {/* Metric 4: Organization Risk Score */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Org Risk Score</span>
            <Flame className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-1">
            <RiskGauge score={metrics.overall_org_risk_score} size="sm" />
          </div>
        </div>
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart 1: Project Risk Comparison */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Project Risk Comparison</h3>
              <p className="text-[11px] text-slate-400">0–100 calculated composite risk scores</p>
            </div>
            <Link href="/projects" className="text-[11px] text-cyan-400 hover:underline">
              View All
            </Link>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={project_risk_comparison} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="project_name" stroke="#64748B" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  itemStyle={{ color: '#38BDF8' }}
                />
                <Bar dataKey="risk_score" radius={[4, 4, 0, 0]}>
                  {project_risk_comparison.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.risk_score >= 80 ? '#EF4444' :
                        entry.risk_score >= 60 ? '#F97316' :
                        entry.risk_score >= 35 ? '#F59E0B' : '#10B981'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Vulnerability Severity Distribution */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Vulnerability Severity Distribution</h3>
              <p className="text-[11px] text-slate-400">OSV database matched security advisories</p>
            </div>
            <Link href="/vulnerabilities" className="text-[11px] text-cyan-400 hover:underline">
              Explore CVEs
            </Link>
          </div>
          <div className="flex h-64 items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severity_distribution}
                  dataKey="count"
                  nameKey="severity"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                >
                  {severity_distribution.map((entry) => (
                    <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] || '#64748B'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 pr-6">
              {severity_distribution.map((item) => (
                <div key={item.severity} className="flex items-center gap-2 text-xs">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[item.severity] }}></span>
                  <span className="text-slate-400 text-[11px] uppercase font-semibold">{item.severity}:</span>
                  <span className="font-bold text-slate-200">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Top Vulnerable Packages & Recent Scan Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Most Vulnerable Packages */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white">Most Vulnerable Packages</h3>
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Priority Remediation</span>
          </div>
          <div className="divide-y divide-slate-800/80">
            {top_vulnerable_packages.length === 0 ? (
              <p className="py-4 text-xs text-slate-500 text-center">No vulnerabilities currently detected.</p>
            ) : (
              top_vulnerable_packages.map((pkg, idx) => (
                <div key={pkg.package_name} className="flex items-center justify-between py-2.5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-slate-800 text-[10px] font-bold text-slate-400">
                      {idx + 1}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-slate-100">{pkg.package_name}</p>
                      <p className="text-[10px] text-slate-400 truncate max-w-xs">
                        {pkg.cve_ids?.slice(0, 2).join(', ') || 'Known OSV Advisory'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-400 border border-rose-500/40">
                      {pkg.vulnerabilities_count} Vuln{pkg.vulnerabilities_count > 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Audit & Scan Activity */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white">Recent Security Activity</h3>
            <Link href="/settings" className="text-[11px] text-cyan-400 hover:underline">
              Audit Trail
            </Link>
          </div>
          <div className="divide-y divide-slate-800/80">
            {recent_activity.slice(0, 5).map((log) => (
              <div key={log.id} className="flex items-start justify-between py-2.5 gap-2">
                <div className="flex items-start gap-2.5">
                  <Activity className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-mono text-cyan-300">
                      {log.action}
                    </span>
                    <p className="text-[11px] text-slate-300 mt-1 line-clamp-1">{log.details}</p>
                  </div>
                </div>
                <span className="text-[10px] text-slate-500 shrink-0 font-mono">
                  {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
