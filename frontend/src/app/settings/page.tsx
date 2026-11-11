'use client';

import React, { useEffect, useState } from 'react';
import {
  Settings,
  ShieldCheck,
  Database,
  Cloud,
  Activity,
  User,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { api } from '../../services/api';

export default function SettingsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCurrentUser(api.getStoredUser());
    api.getActivityLogs()
      .then((data) => setLogs(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Settings className="h-5 w-5 text-cyan-400" />
          <span>Settings, Cloud Architecture & Compliance Audit</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Identity management, Role-Based Access Control (RBAC), and security audit trails
        </p>
      </div>

      {/* Grid: Identity Profile & Cloud Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* User Identity Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400">
              <User className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Active Session & Identity</h3>
              <p className="text-xs text-slate-400">Authenticated via JWT Bearer Token</p>
            </div>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Full Name:</span>
              <span className="font-semibold text-slate-200">{currentUser?.full_name || 'Administrator'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Email Address:</span>
              <span className="font-semibold text-slate-200">{currentUser?.email || 'admin@dependencyx.io'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Assigned Role (RBAC):</span>
              <span className="rounded bg-cyan-950 border border-cyan-800 px-2 py-0.5 text-[10px] font-bold text-cyan-300 uppercase">
                {currentUser?.role || 'admin'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Password Hashing:</span>
              <span className="font-mono text-slate-400">bcrypt (Cost Factor 12)</span>
            </div>
          </div>
        </div>

        {/* Cloud & Database Architecture Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/20 text-blue-400">
              <Cloud className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Cloud Infrastructure & DP-900</h3>
              <p className="text-xs text-slate-400">Azure Data Services & Local Resilience</p>
            </div>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-cyan-400" />
                <span className="text-slate-300">Relational Database:</span>
              </div>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> 3NF Normalization Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cloud className="h-4 w-4 text-cyan-400" />
                <span className="text-slate-300">Blob Storage Adapter:</span>
              </div>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Azure Blob / Local Storage Fallback
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-cyan-400" />
                <span className="text-slate-300">Data Isolation:</span>
              </div>
              <span className="text-slate-300">Multi-tenant Organization Scoping</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Activity Logs Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Immutable Security Audit Trail</h3>
          </div>
          <span className="text-[11px] text-slate-500">Persisted in Activity_Logs table</span>
        </div>

        {loading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950/60 text-[10px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Action</th>
                  <th className="px-4 py-3 font-semibold">Entity Type</th>
                  <th className="px-4 py-3 font-semibold">Audit Details</th>
                  <th className="px-4 py-3 font-semibold">IP Address</th>
                  <th className="px-4 py-3 font-semibold">Timestamp (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-cyan-300 font-bold">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-slate-400">{log.entity_type}</td>
                    <td className="px-4 py-3 font-sans text-slate-200">{log.details}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-slate-500">{log.ip_address || '127.0.0.1'}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-slate-500">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
