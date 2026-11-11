'use client';

import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { ShieldAlert, ShieldCheck, Box, Layers, AlertTriangle } from 'lucide-react';
import { GraphNodeData } from '../types';

interface DependencyNodeProps {
  data: GraphNodeData;
  selected: boolean;
}

export const DependencyNode = memo(({ data, selected }: DependencyNodeProps) => {
  const isRoot = data.node_type === 'project_root';
  const isVuln = data.is_vulnerable;
  const severity = data.highest_severity || 'NONE';

  // Severity border and background colors
  let borderColor = 'border-slate-700';
  let badgeBg = 'bg-slate-800 text-slate-400';

  if (isRoot) {
    borderColor = 'border-cyan-500 shadow-cyan-500/20';
  } else if (isVuln) {
    if (severity === 'CRITICAL') {
      borderColor = 'border-rose-500 shadow-rose-500/30';
      badgeBg = 'bg-rose-500/20 text-rose-400 border border-rose-500/40';
    } else if (severity === 'HIGH') {
      borderColor = 'border-orange-500 shadow-orange-500/30';
      badgeBg = 'bg-orange-500/20 text-orange-400 border border-orange-500/40';
    } else if (severity === 'MEDIUM') {
      borderColor = 'border-amber-500 shadow-amber-500/30';
      badgeBg = 'bg-amber-500/20 text-amber-400 border border-amber-500/40';
    } else {
      borderColor = 'border-emerald-500 shadow-emerald-500/20';
      badgeBg = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
    }
  }

  return (
    <div
      className={`min-w-[210px] max-w-[260px] rounded-xl border bg-slate-900/95 p-3.5 shadow-xl backdrop-blur-md transition-all duration-200 ${borderColor} ${
        selected ? 'ring-2 ring-cyan-400 shadow-cyan-500/40' : ''
      } ${isVuln ? 'animate-pulse-subtle' : ''}`}
    >
      <Handle type="target" position={Position.Top} className="!bg-cyan-500 !w-2.5 !h-2.5 !border-slate-900" />

      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          {isRoot ? (
            <div className="rounded-lg bg-cyan-500/20 p-1.5 text-cyan-400">
              <Box className="h-4 w-4" />
            </div>
          ) : isVuln ? (
            <div className="rounded-lg bg-rose-500/20 p-1.5 text-rose-400">
              <ShieldAlert className="h-4 w-4" />
            </div>
          ) : (
            <div className="rounded-lg bg-slate-800 p-1.5 text-slate-400">
              <Layers className="h-4 w-4" />
            </div>
          )}
          <div className="overflow-hidden">
            <h4 className="truncate text-xs font-semibold text-slate-100" title={data.label}>
              {data.label}
            </h4>
            <p className="truncate text-[10px] text-slate-400">v{data.version}</p>
          </div>
        </div>

        {/* Depth / Direct Pill */}
        {!isRoot && (
          <span
            className={`rounded-full px-2 py-0.5 text-[9px] font-medium ${
              data.is_direct ? 'bg-cyan-950 text-cyan-300 border border-cyan-800' : 'bg-slate-800 text-slate-400'
            }`}
          >
            {data.is_direct ? 'Direct' : `L${data.depth || 2}`}
          </span>
        )}
      </div>

      {/* Vulnerability status banner */}
      {isVuln && (
        <div className="mt-2.5 flex items-center justify-between rounded-lg bg-slate-950/60 px-2 py-1 border border-slate-800">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="h-3 w-3 text-rose-400" />
            <span className="text-[10px] font-medium text-slate-300">
              {data.vulnerabilities?.length || 1} CVE{data.vulnerabilities && data.vulnerabilities.length > 1 ? 's' : ''}
            </span>
          </div>
          <span className={`rounded px-1.5 py-0.2 text-[9px] font-bold tracking-wide uppercase ${badgeBg}`}>
            {severity}
          </span>
        </div>
      )}

      {/* Clean status badge */}
      {!isVuln && !isRoot && (
        <div className="mt-2.5 flex items-center gap-1 text-[10px] text-emerald-400/90 font-medium">
          <ShieldCheck className="h-3 w-3" />
          <span>No known CVE</span>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-cyan-500 !w-2.5 !h-2.5 !border-slate-900" />
    </div>
  );
});

DependencyNode.displayName = 'DependencyNode';
