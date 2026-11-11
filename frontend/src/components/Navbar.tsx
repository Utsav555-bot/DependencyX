'use client';

import React from 'react';
import { Database, Plus, RefreshCw, Shield, UserCheck } from 'lucide-react';

interface NavbarProps {
  onOpenCreateProject: () => void;
  onRefresh?: () => void;
  user?: any;
  onSwitchRole?: (role: 'admin' | 'developer') => void;
}

export const Navbar = ({ onOpenCreateProject, onRefresh, user, onSwitchRole }: NavbarProps) => {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-8 backdrop-blur-md">
      {/* Status Bar */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
          <Database className="h-3.5 w-3.5 text-cyan-400" />
          <span className="font-medium">RDBMS (3NF):</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Connected
          </span>
        </div>

        <div className="hidden md:flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-400">
          <Shield className="h-3.5 w-3.5 text-cyan-400" />
          <span>OSV.dev Vulnerability Engine: Active</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        {/* Quick Role Switcher for Academic Viva Demonstration */}
        {user && onSwitchRole && (
          <div className="hidden lg:flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
            <UserCheck className="h-3.5 w-3.5 text-slate-400 ml-1.5" />
            <span className="text-[11px] text-slate-400 font-medium">Demo Role:</span>
            <button
              onClick={() => onSwitchRole('admin')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                user.role === 'admin' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Admin
            </button>
            <button
              onClick={() => onSwitchRole('developer')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                user.role === 'developer' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Developer
            </button>
          </div>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-white transition"
            title="Refresh Data"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        )}

        <button
          onClick={onOpenCreateProject}
          className="flex items-center gap-2 rounded-lg bg-cyan-600 px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-600/20 hover:bg-cyan-500 transition"
        >
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </button>
      </div>
    </header>
  );
};
