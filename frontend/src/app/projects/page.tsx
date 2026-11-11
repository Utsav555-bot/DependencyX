'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FolderGit2,
  Search,
  Plus,
  Play,
  Network,
  Download,
  Trash2,
  ExternalLink,
  ShieldAlert,
  Loader2,
  AlertCircle,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '../../services/api';
import { Project } from '../../types';
import { RiskGauge } from '../../components/RiskGauge';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleTriggerScan = async (projectId: string) => {
    setScanningId(projectId);
    setScanMessage(null);
    try {
      const res = await api.triggerScan(projectId);
      setScanMessage(`Scan complete for project: ${res.vulnerable_packages_count} vulnerable packages detected. Risk score: ${res.overall_risk_score}/100.`);
      await loadProjects();
    } catch (err: any) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setScanningId(null);
    }
  };

  const handleDeleteProject = async (projectId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete project "${name}"? This will delete all parsed dependency edges and scan history.`)) {
      return;
    }
    try {
      await api.deleteProject(projectId);
      await loadProjects();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <FolderGit2 className="h-5 w-5 text-cyan-400" />
            <span>Monitored Software Projects</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise application inventory with continuous dependency auditing
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search projects..."
            className="w-full rounded-lg border border-slate-800 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Notifications */}
      {scanMessage && (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-950/40 p-4 text-xs text-cyan-200 flex items-center justify-between">
          <span>{scanMessage}</span>
          <button onClick={() => setScanMessage(null)} className="text-cyan-400 hover:text-white font-bold ml-4">
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Projects Grid */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <FolderGit2 className="mx-auto h-12 w-12 text-slate-600 mb-3" />
          <h3 className="text-sm font-bold text-slate-200">No Projects Found</h3>
          <p className="text-xs text-slate-500 mt-1">Create your first software project or upload a package-lock.json.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl transition-all hover:border-slate-700 hover:shadow-cyan-500/5"
            >
              <div>
                {/* Project Header */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-white hover:text-cyan-400 transition">
                      <Link href={`/graph?project=${project.id}`}>{project.name}</Link>
                    </h3>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-300">
                        {project.ecosystem}
                      </span>
                      {project.repository_url && (
                        <a
                          href={project.repository_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-slate-400 hover:text-cyan-400 flex items-center gap-0.5"
                        >
                          <ExternalLink className="h-2.5 w-2.5" />
                          <span>Repo</span>
                        </a>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteProject(project.id, project.name)}
                    className="rounded-lg p-1 text-slate-500 hover:bg-slate-800 hover:text-rose-400 transition"
                    title="Delete Project"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <p className="mt-3 text-xs text-slate-400 line-clamp-2">
                  {project.description || 'No description provided for this software application.'}
                </p>

                {/* Risk Gauge Bar */}
                <div className="mt-4 border-t border-slate-800/80 pt-3">
                  <RiskGauge score={project.risk_score} level={project.risk_level} size="sm" />
                </div>

                {/* Dependency & Vuln Counters */}
                <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/60 text-center">
                  <div>
                    <p className="text-[10px] font-medium text-slate-400">Dependencies</p>
                    <p className="text-sm font-bold text-slate-200 mt-0.5">{project.total_dependencies}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium text-slate-400">Vulnerable Pkgs</p>
                    <p className={`text-sm font-bold mt-0.5 ${project.vulnerable_packages_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {project.vulnerable_packages_count}
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="mt-5 flex items-center justify-between border-t border-slate-800/80 pt-3 gap-2">
                <Link
                  href={`/graph?project=${project.id}`}
                  className="flex items-center gap-1.5 rounded-lg border border-cyan-800/50 bg-cyan-950/30 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/40 transition"
                >
                  <Network className="h-3.5 w-3.5" />
                  <span>Graph Map</span>
                </Link>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleTriggerScan(project.id)}
                    disabled={scanningId === project.id}
                    className="flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition disabled:opacity-50"
                    title="Run OSV Vulnerability Scan"
                  >
                    {scanningId === project.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                    ) : (
                      <Play className="h-3 w-3 text-emerald-400" />
                    )}
                    <span>Scan</span>
                  </button>

                  <a
                    href={api.getExportUrl(project.id, 'csv')}
                    download
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
                    title="Export CSV Audit Report"
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
