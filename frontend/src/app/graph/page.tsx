'use client';

import React, { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  NodeMouseHandler
} from 'reactflow';
import 'reactflow/dist/style.css';

import {
  Network,
  ShieldAlert,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  AlertTriangle,
  Play,
  Info,
  CheckCircle2,
  ExternalLink,
  Loader2,
  X
} from 'lucide-react';
import { api } from '../../services/api';
import { DependencyNode } from '../../components/DependencyNode';
import { Project, GraphResponse } from '../../types';

function DependencyGraphContent() {
  const searchParams = useSearchParams();
  const initialProjectId = searchParams.get('project');

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(initialProjectId || '');
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const nodeTypes = useMemo(() => ({ customDependency: DependencyNode }), []);

  // Fetch projects list
  useEffect(() => {
    api.getProjects()
      .then((data) => {
        setProjects(data);
        if (!selectedProjectId && data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  // Fetch graph whenever selectedProjectId changes
  const loadGraph = useCallback(async (projId: string) => {
    if (!projId) return;
    setLoading(true);
    setError(null);
    setSelectedNodeData(null);

    try {
      const data = await api.getGraph(projId);
      setGraphData(data);
      setNodes(data.nodes as Node[]);
      setEdges(data.edges as Edge[]);
    } catch (err: any) {
      setError(err.message || 'Failed to render dependency graph');
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    if (selectedProjectId) {
      loadGraph(selectedProjectId);
    }
  }, [selectedProjectId, loadGraph]);

  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNodeData(node.data);
  }, []);

  const handleTriggerScan = async () => {
    if (!selectedProjectId) return;
    setScanning(true);
    try {
      await api.triggerScan(selectedProjectId);
      await loadGraph(selectedProjectId);
    } catch (err: any) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="relative flex h-[calc(100vh-6rem)] flex-col space-y-4 animate-in fade-in duration-300">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Dependency Graph Explorer</h1>
            <p className="text-[11px] text-slate-400">
              Interactive topological risk map &bull; NetworkX directed graph analysis
            </p>
          </div>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.total_dependencies} deps)
              </option>
            ))}
          </select>

          <button
            onClick={handleTriggerScan}
            disabled={scanning || !selectedProjectId}
            className="flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-cyan-600/20 hover:bg-cyan-500 transition disabled:opacity-50"
          >
            {scanning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            <span>Scan OSV Vulnerabilities</span>
          </button>
        </div>
      </div>

      {/* Circular Dependency Warning Alert */}
      {graphData?.summary.has_circular && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-300 animate-pulse">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>
            <strong>Circular Dependency Detected!</strong> Cycle detected in imported graph:{' '}
            {graphData.summary.circular_dependencies.join(' | ')}
          </span>
        </div>
      )}

      {/* Graph Area */}
      <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
              <p className="text-xs text-slate-400">Computing NetworkX graph layout & depths...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center p-6 text-center">
            <div>
              <AlertTriangle className="mx-auto h-8 w-8 text-rose-400 mb-2" />
              <h3 className="text-sm font-bold text-white">Graph Rendering Error</h3>
              <p className="text-xs text-slate-400 mt-1">{error}</p>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            minZoom={0.2}
            maxZoom={1.8}
          >
            <Background color="#1E293B" gap={24} size={1} />
            <Controls className="!bg-slate-900 !border-slate-800" />
            <MiniMap
              nodeColor={(n: any) => {
                if (n.data?.is_vulnerable) return '#EF4444';
                if (n.data?.is_direct) return '#06B6D4';
                return '#475569';
              }}
              maskColor="rgba(15, 23, 42, 0.75)"
              className="!bg-slate-950 !border !border-slate-800 !rounded-lg"
            />
          </ReactFlow>
        )}

        {/* Graph Legend Overlay */}
        <div className="absolute bottom-4 left-4 z-10 flex flex-wrap items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/90 px-3.5 py-2 text-[10px] text-slate-300 backdrop-blur-md shadow-lg">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
            <span>Direct Dependency</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-slate-500"></span>
            <span>Transitive</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
            <span>Vulnerable (OSV Detected)</span>
          </div>
          <div className="flex items-center gap-1.5 border-l border-slate-700 pl-3 text-slate-400">
            <span>Max Tree Depth: <strong>{graphData?.summary.max_depth || 1}</strong></span>
          </div>
        </div>

        {/* Package Details Slide-Out Drawer */}
        {selectedNodeData && (
          <div className="absolute right-4 top-4 z-20 w-80 max-h-[calc(100%-2rem)] overflow-y-auto rounded-xl border border-slate-700 bg-slate-900/95 p-5 shadow-2xl backdrop-blur-xl animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Package Telemetry</h3>
              </div>
              <button
                onClick={() => setSelectedNodeData(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <p className="text-[10px] uppercase font-semibold text-slate-500">Package Identifier</p>
                <h4 className="text-sm font-bold text-cyan-300 break-all">{selectedNodeData.label}</h4>
                <p className="text-xs text-slate-400">Version: {selectedNodeData.version}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                <div>
                  <p className="text-[10px] text-slate-500">Dependency Nature</p>
                  <p className="text-xs font-bold text-slate-200">{selectedNodeData.is_direct ? 'Direct' : 'Transitive'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">Tree Depth</p>
                  <p className="text-xs font-bold text-slate-200">Level {selectedNodeData.depth || 1}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">Betweenness Centrality</p>
                  <p className="text-xs font-bold text-cyan-400">{selectedNodeData.betweenness || 0.0}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">In / Out Degree</p>
                  <p className="text-xs font-bold text-slate-200">{selectedNodeData.in_degree || 0} / {selectedNodeData.out_degree || 0}</p>
                </div>
              </div>

              {/* Vulnerabilities Section */}
              <div className="border-t border-slate-800 pt-3">
                <p className="text-[10px] uppercase font-semibold text-slate-500 mb-2">OSV Vulnerability Analysis</p>
                {selectedNodeData.is_vulnerable && selectedNodeData.vulnerabilities?.length > 0 ? (
                  <div className="space-y-2.5">
                    {selectedNodeData.vulnerabilities.map((v: any, idx: number) => (
                      <div key={idx} className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-rose-300">{v.cve_id || v.osv_id}</span>
                          <span className="rounded bg-rose-500/30 px-1.5 py-0.2 text-[9px] font-bold text-rose-300 uppercase">
                            {v.severity}
                          </span>
                        </div>
                        <p className="mt-1.5 text-[11px] text-slate-300 leading-snug">{v.summary}</p>
                        {v.fixed_version && (
                          <p className="mt-2 text-[10px] text-emerald-400 font-medium">
                            Patched in version: <strong>{v.fixed_version}</strong>
                          </p>
                        )}
                        <a
                          href={`https://osv.dev/vulnerability/${v.osv_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-[10px] text-cyan-400 hover:underline"
                        >
                          <span>OSV Advisory</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>No known vulnerability detected in this scan.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DependencyGraphPage() {
  return (
    <Suspense fallback={
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent"></div>
          <p className="text-xs text-slate-400">Loading Dependency Graph Explorer...</p>
        </div>
      </div>
    }>
      <DependencyGraphContent />
    </Suspense>
  );
}
