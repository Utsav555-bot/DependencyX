'use client';

import React, { useState } from 'react';
import { X, Upload, FolderPlus, AlertCircle, CheckCircle2, Loader2, FileCode } from 'lucide-react';
import { api } from '../services/api';

interface ProjectUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  projects?: any[];
}

export const ProjectUploadModal = ({ isOpen, onClose, onSuccess, projects = [] }: ProjectUploadModalProps) => {
  const [tab, setTab] = useState<'create' | 'upload'>('create');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState(projects[0]?.id || '');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const created = await api.createProject({
        name,
        description,
        repository_url: repoUrl,
        ecosystem: 'npm'
      });
      setSuccess(`Project "${created.name}" created! Now upload a package-lock.json to map dependencies.`);
      setSelectedProjectId(created.id);
      setTab('upload');
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadManifest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) {
      setError('Please select or create a project first.');
      return;
    }
    if (!file) {
      setError('Please select a package-lock.json file.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const result = await api.uploadManifest(selectedProjectId, file);
      setSuccess(`Manifest parsed! Extracted ${result.total_packages} packages and ${result.total_dependencies} dependency relationships.`);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to upload manifest');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-cyan-500/20 p-2 text-cyan-400">
              <FolderPlus className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Project & Manifest Manager</h3>
              <p className="text-xs text-slate-400">Add application or ingest npm lockfile</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-800 mt-4">
          <button
            onClick={() => { setTab('create'); setError(null); }}
            className={`flex-1 pb-2.5 text-xs font-semibold transition border-b-2 ${
              tab === 'create' ? 'border-cyan-500 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            1. Create Project
          </button>
          <button
            onClick={() => { setTab('upload'); setError(null); }}
            className={`flex-1 pb-2.5 text-xs font-semibold transition border-b-2 ${
              tab === 'upload' ? 'border-cyan-500 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            2. Upload Manifest (package-lock.json)
          </button>
        </div>

        {/* Notifications */}
        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{success}</span>
          </div>
        )}

        {/* Tab 1: Create Project */}
        {tab === 'create' && (
          <form onSubmit={handleCreateProject} className="mt-4 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Project Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Payment Microservice"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe this application's security perimeter and architectural role..."
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Repository URL (Optional)</label>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/org/repo"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg px-4 py-2 text-xs font-medium text-slate-400 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white hover:bg-cyan-500 transition disabled:opacity-50"
              >
                {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                <span>Create & Continue</span>
              </button>
            </div>
          </form>
        )}

        {/* Tab 2: Upload Manifest */}
        {tab === 'upload' && (
          <form onSubmit={handleUploadManifest} className="mt-4 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Select Target Project *</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.ecosystem})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Upload package-lock.json *</label>
              <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950/60 p-6 text-center hover:border-cyan-500/50 transition">
                <FileCode className="h-8 w-8 text-cyan-400 mb-2" />
                <p className="text-xs font-semibold text-slate-200">
                  {file ? file.name : 'Select or drag package-lock.json'}
                </p>
                <p className="text-[11px] text-slate-500 mt-1">Supports npm lockfile version 1, 2, and 3</p>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setFile(e.target.files[0]);
                    }
                  }}
                  className="mt-3 block text-xs text-slate-400 file:mr-2 file:rounded-md file:border-0 file:bg-slate-800 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg px-4 py-2 text-xs font-medium text-slate-400 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !file}
                className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white hover:bg-cyan-500 transition disabled:opacity-50"
              >
                {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                <Upload className="h-3.5 w-3.5" />
                <span>Upload & Parse Manifest</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
