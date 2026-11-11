'use client';

import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Calendar,
  Layers
} from 'lucide-react';
import { api } from '../../services/api';
import { VulnerabilityItem } from '../../types';

export default function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState<VulnerabilityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getAllVulnerabilities()
      .then((data) => setVulns(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredVulns = vulns.filter((v) => {
    const matchesSearch =
      v.affected_package.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.osv_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (v.cve_id && v.cve_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (v.summary && v.summary.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesSeverity = severityFilter === 'ALL' || v.severity === severityFilter;

    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-rose-400" />
            <span>Vulnerability Detection Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time synchronization with Open Source Vulnerabilities (OSV) API &bull; CVE & GHSA registry
          </p>
        </div>

        {/* Search & Severity Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search CVE, package, or summary..."
              className="w-full rounded-lg border border-slate-800 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900 p-1">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`rounded px-2.5 py-1 text-[11px] font-semibold transition ${
                  severityFilter === sev
                    ? 'bg-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Table */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
        </div>
      ) : filteredVulns.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-emerald-400 mb-3" />
          <h3 className="text-sm font-bold text-slate-200">No Known Vulnerabilities Found</h3>
          <p className="text-xs text-slate-500 mt-1">No vulnerabilities matched your current filter criteria.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950/60 text-[10px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Severity & CVSS</th>
                  <th className="px-4 py-3 font-semibold">Identifiers</th>
                  <th className="px-4 py-3 font-semibold">Affected Package</th>
                  <th className="px-4 py-3 font-semibold">Vulnerability Summary</th>
                  <th className="px-4 py-3 font-semibold">Affected Range</th>
                  <th className="px-4 py-3 font-semibold">Fixed Version</th>
                  <th className="px-4 py-3 font-semibold">Advisory</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredVulns.map((v) => {
                  let sevBg = 'bg-slate-800 text-slate-400 border-slate-700';
                  if (v.severity === 'CRITICAL') sevBg = 'bg-rose-500/20 text-rose-400 border-rose-500/40';
                  else if (v.severity === 'HIGH') sevBg = 'bg-orange-500/20 text-orange-400 border-orange-500/40';
                  else if (v.severity === 'MEDIUM') sevBg = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
                  else if (v.severity === 'LOW') sevBg = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';

                  return (
                    <tr key={v.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className={`rounded border px-2 py-0.5 text-[9px] font-bold uppercase ${sevBg}`}>
                            {v.severity}
                          </span>
                          {v.cvss_score && (
                            <span className="font-mono text-[11px] font-bold text-slate-400">
                              {v.cvss_score.toFixed(1)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="font-bold text-white">{v.cve_id || v.osv_id}</div>
                        {v.ghsa_id && v.ghsa_id !== v.cve_id && (
                          <div className="text-[10px] text-slate-500 font-mono">{v.ghsa_id}</div>
                        )}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 font-bold text-cyan-300">
                          <Layers className="h-3.5 w-3.5 text-cyan-400" />
                          <span>{v.affected_package}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 max-w-xs truncate text-slate-300" title={v.summary || ''}>
                        {v.summary || 'Known vulnerability recorded in ecosystem.'}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap font-mono text-[11px] text-slate-400">
                        {v.affected_range || 'All affected'}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {v.fixed_version ? (
                          <span className="rounded bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                            v{v.fixed_version}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Unpatched</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <a
                          href={`https://osv.dev/vulnerability/${v.osv_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-[11px] text-cyan-400 hover:underline"
                        >
                          <span>OSV</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
