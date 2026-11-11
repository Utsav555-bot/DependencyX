'use client';

import React, { useEffect, useState } from 'react';
import {
  Flame,
  AlertTriangle,
  GitFork,
  Layers,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Sliders,
  CheckCircle2,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { api } from '../../services/api';
import { Project, RiskDetails } from '../../types';
import { RiskGauge } from '../../components/RiskGauge';

export default function RiskAnalysisPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [riskData, setRiskData] = useState<RiskDetails | null>(null);
  const [criticalDeps, setCriticalDeps] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects()
      .then((data) => {
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));

    api.getCriticalDependencies()
      .then((data) => setCriticalDeps(data))
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    setLoading(true);
    api.getProjectRisk(selectedProjectId)
      .then((data) => setRiskData(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedProjectId]);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Flame className="h-5 w-5 text-amber-400" />
            <span>Risk Analysis & Vulnerability Propagation Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            NetworkX graph traversal &bull; Multi-factor contextual risk scoring (0–100) &bull; Single Points of Failure
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium">Target Project:</label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
        </div>
      ) : error || !riskData ? (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-center text-xs text-rose-300">
          {error || 'No risk assessment data available.'}
        </div>
      ) : (
        <>
          {/* Risk Summary Cards */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            {/* Overall Composite Score */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Project Composite Risk</h3>
              <RiskGauge score={riskData.overall_score} level={riskData.risk_level} size="lg" />
              <p className="mt-4 text-[11px] text-slate-400 leading-relaxed">
                Calculated using four transparent weighted dimensions: Peak Vulnerability (45%), Propagation & Cross-Project Usage (25%), Graph Depth (15%), and Single Point of Failure Penalty (15%).
              </p>
            </div>

            {/* Risk Factor Breakdown */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Mathematical Factor Breakdown</h3>
              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                  <span className="text-slate-400">Peak Severity Component (45%):</span>
                  <span className="font-mono font-bold text-rose-400">{riskData.breakdown.vulnerability_component || 0} pts</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                  <span className="text-slate-400">Propagation & Blast Radius (25%):</span>
                  <span className="font-mono font-bold text-orange-400">{riskData.breakdown.propagation_component || 0} pts</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5">
                  <span className="text-slate-400">Dependency Depth Footprint (15%):</span>
                  <span className="font-mono font-bold text-cyan-400">{riskData.breakdown.depth_footprint || 0} pts</span>
                </div>
                <div className="flex items-center justify-between pb-1">
                  <span className="text-slate-400">SPOF & Centrality Penalty (15%):</span>
                  <span className="font-mono font-bold text-amber-400">{riskData.breakdown.spof_penalty || 0} pts</span>
                </div>
              </div>
            </div>

            {/* Depth & Propagation Metrics */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Graph Topology Profile</h3>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Max Graph Depth</p>
                  <p className="text-xl font-bold text-cyan-400 mt-1">Level {riskData.max_depth}</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">SPOF Count</p>
                  <p className="text-xl font-bold text-rose-400 mt-1">{riskData.spof_count}</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Direct Vulns</p>
                  <p className="text-xl font-bold text-slate-200 mt-1">{riskData.direct_vulnerabilities}</p>
                </div>
                <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Transitive Vulns</p>
                  <p className="text-xl font-bold text-slate-200 mt-1">{riskData.transitive_vulnerabilities}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Vulnerability Reverse Propagation Traversal */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <GitFork className="h-4 w-4 text-cyan-400" />
                  <span>Reverse Vulnerability Propagation Paths</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Traces how compromised packages propagate upstream to root applications
                </p>
              </div>
              <span className="rounded bg-cyan-950 px-2.5 py-1 text-[11px] font-semibold text-cyan-300 border border-cyan-800">
                NetworkX Reverse Traversal
              </span>
            </div>

            {riskData.vulnerable_packages.length === 0 ? (
              <div className="rounded-lg bg-slate-950/60 p-6 text-center text-xs text-emerald-400">
                <CheckCircle2 className="mx-auto h-6 w-6 mb-2" />
                No vulnerable packages detected in this project dependency graph.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {riskData.vulnerable_packages.map((v: any, idx: number) => (
                  <div key={idx} className="py-4 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="rounded bg-rose-500/20 border border-rose-500/40 px-2 py-0.5 text-[10px] font-bold text-rose-400 uppercase">
                          {v.severity}
                        </span>
                        <h4 className="text-xs font-bold text-white">
                          {v.package_name} <span className="text-slate-400 font-normal">v{v.version}</span>
                        </h4>
                        <span className="text-[10px] text-slate-500">
                          ({v.is_direct ? 'Direct Dependency' : `Transitive at Depth ${v.depth}`})
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-400">Calculated Risk:</span>
                        <span className="font-mono text-xs font-bold text-amber-400">{v.calculated_risk}/100</span>
                      </div>
                    </div>

                    <p className="mt-2 text-xs text-slate-300">{v.summary}</p>

                    {/* Propagation Chain */}
                    <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg bg-slate-950 p-2.5 text-xs border border-slate-800/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-500">Propagation Path:</span>
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-bold text-cyan-300">
                        {riskData.project_name} (Root)
                      </span>
                      {v.upstream_dependents && v.upstream_dependents.length > 0 ? (
                        v.upstream_dependents.map((depName: string) => (
                          <React.Fragment key={depName}>
                            <ArrowRight className="h-3 w-3 text-slate-500" />
                            <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[11px] text-slate-300">
                              {depName}
                            </span>
                          </React.Fragment>
                        ))
                      ) : (
                        <ArrowRight className="h-3 w-3 text-slate-500" />
                      )}
                      <ArrowRight className="h-3 w-3 text-rose-400" />
                      <span className="rounded bg-rose-950/60 border border-rose-800 px-2 py-0.5 text-[11px] font-bold text-rose-300">
                        {v.package_name} (Vulnerable Target)
                      </span>
                    </div>

                    <div className="mt-2 text-[10px] text-slate-400 flex items-center gap-4">
                      <span>Affected Organization Projects: <strong>{v.affected_projects_count}</strong></span>
                      {v.fixed_version && (
                        <span>Remediation Version: <strong className="text-emerald-400">v{v.fixed_version}</strong></span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Organization Critical Dependencies & Single Points of Failure */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-400" />
                  <span>Single Points of Failure (SPOF) & Critical Dependencies</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Packages shared by multiple applications or possessing high graph centrality
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 bg-slate-950/60 text-[10px] uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Classification</th>
                    <th className="px-4 py-3 font-semibold">Package Name</th>
                    <th className="px-4 py-3 font-semibold">Affected Projects</th>
                    <th className="px-4 py-3 font-semibold">Active Vulnerability</th>
                    <th className="px-4 py-3 font-semibold">Classification Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {criticalDeps.map((dep, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3 whitespace-nowrap">
                        {dep.is_single_point_of_failure ? (
                          <span className="rounded bg-rose-500/20 border border-rose-500/40 px-2 py-0.5 text-[9px] font-bold text-rose-400 uppercase">
                            Single Point of Failure
                          </span>
                        ) : (
                          <span className="rounded bg-amber-500/20 border border-amber-500/40 px-2 py-0.5 text-[9px] font-bold text-amber-400 uppercase">
                            Critical Dependency
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-bold text-white whitespace-nowrap">
                        {dep.package_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono font-bold text-cyan-300">
                          {dep.affected_projects_count} Projects
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {dep.has_vulnerability ? (
                          <span className="text-rose-400 font-semibold">{dep.highest_severity} CVE</span>
                        ) : (
                          <span className="text-emerald-400 font-semibold">Patched</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {dep.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
