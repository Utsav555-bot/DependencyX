'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Eye,
  CheckCircle2,
  Cloud,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { api } from '../../services/api';
import { Project } from '../../types';

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [htmlReport, setHtmlReport] = useState<string>('');
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
  }, []);

  const loadHtmlReport = async (projId: string) => {
    if (!projId) return;
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/reports/${projId}`);
      if (res.ok) {
        const text = await res.text();
        setHtmlReport(text);
      }
    } catch (err: any) {
      console.error('Error fetching HTML report', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadHtmlReport(selectedProjectId);
    }
  }, [selectedProjectId]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileText className="h-5 w-5 text-cyan-400" />
            <span>Compliance & Security Audit Reports</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Exportable executive summaries, CSV dependency audits &bull; DP-900 Unstructured Data Store
          </p>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex flex-wrap items-center gap-3">
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

          {selectedProjectId && (
            <div className="flex items-center gap-2">
              <a
                href={api.getExportUrl(selectedProjectId, 'csv')}
                download
                className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
              >
                <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                <span>Export CSV</span>
              </a>

              <a
                href={api.getExportUrl(selectedProjectId, 'html')}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-cyan-500 transition shadow-lg shadow-cyan-600/20"
              >
                <Download className="h-4 w-4" />
                <span>Download Report</span>
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Cloud Compliance Info Banner */}
      <div className="rounded-xl border border-cyan-900/40 bg-cyan-950/20 p-4">
        <div className="flex items-center gap-2 text-xs font-bold text-cyan-300">
          <Cloud className="h-4 w-4 text-cyan-400" />
          <span>DP-900 Data Architecture Compliance</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Generated compliance reports represent <strong>Unstructured Data</strong> archived in Microsoft Azure Blob Storage (Cool Access Tier). Structured dependency records are preserved in Azure SQL Database (3NF).
        </p>
      </div>

      {/* Live Report Preview Frame */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Eye className="h-4 w-4 text-cyan-400" />
            <span>Executive Report Preview</span>
          </h3>
          <span className="text-[11px] text-slate-500">Rendered from Database Metrics</span>
        </div>

        {loading ? (
          <div className="flex h-96 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
            <iframe
              srcDoc={htmlReport}
              title="Report Preview"
              className="h-[600px] w-full border-0"
            />
          </div>
        )}
      </div>
    </div>
  );
}
