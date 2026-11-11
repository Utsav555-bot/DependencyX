'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Shield,
  Layers,
  Flame,
  FileSpreadsheet,
  Download,
  Loader2,
  AlertCircle
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
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts';
import { api } from '../../services/api';
import { DashboardAnalytics } from '../../types';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#EF4444',
  HIGH: '#F97316',
  MEDIUM: '#F59E0B',
  LOW: '#10B981',
};

export default function AnalyticsPage() {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getDashboardAnalytics()
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-center text-xs text-rose-300">
        <AlertCircle className="mx-auto h-8 w-8 mb-2" />
        <span>{error || 'Failed to load security analytics.'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-cyan-400" />
            <span>Cybersecurity Analytics & Trend Telemetry</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Database-derived security metrics &bull; Dependency depth distribution &bull; Real-time vulnerability posture
          </p>
        </div>
      </div>

      {/* Top 3 High-Level Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
          <p className="text-xs font-semibold text-slate-400 uppercase">Total Tracked Dependencies</p>
          <p className="mt-2 text-3xl font-bold text-cyan-400">{data.metrics.total_dependencies}</p>
          <p className="text-[11px] text-slate-500 mt-1">Across {data.metrics.total_projects} projects</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
          <p className="text-xs font-semibold text-slate-400 uppercase">Vulnerable Package Rate</p>
          <p className="mt-2 text-3xl font-bold text-rose-400">
            {data.metrics.total_unique_packages > 0
              ? `${Math.round((data.metrics.vulnerable_packages / data.metrics.total_unique_packages) * 100)}%`
              : '0%'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            {data.metrics.vulnerable_packages} of {data.metrics.total_unique_packages} unique packages
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
          <p className="text-xs font-semibold text-slate-400 uppercase">High/Critical Risk Applications</p>
          <p className="mt-2 text-3xl font-bold text-amber-400">{data.metrics.high_risk_projects}</p>
          <p className="text-[11px] text-slate-500 mt-1">Projects requiring active patching</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart 1: Dependency Depth Distribution */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white">Dependency Depth Distribution</h3>
            <p className="text-[11px] text-slate-400">Package count grouped by tree depth from root</p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.depth_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="depth" stroke="#64748B" fontSize={11} tickFormatter={(val) => `Level ${val}`} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="count" fill="#06B6D4" radius={[4, 4, 0, 0]} name="Packages" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Project Risk Score Comparison */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white">Project Risk Comparison</h3>
            <p className="text-[11px] text-slate-400">Evaluated 0–100 composite risk scores</p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.project_risk_comparison} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="project_name" stroke="#64748B" fontSize={10} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={11} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="risk_score" radius={[4, 4, 0, 0]} name="Risk Score">
                  {data.project_risk_comparison.map((entry, idx) => (
                    <Cell
                      key={idx}
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
      </div>
    </div>
  );
}
