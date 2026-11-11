'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FolderGit2,
  Network,
  ShieldAlert,
  Flame,
  BarChart3,
  FileText,
  Settings,
  ShieldCheck,
  LogOut,
  User as UserIcon,
  Cloud
} from 'lucide-react';
import { api } from '../services/api';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderGit2 },
  { name: 'Dependency Graph', href: '/graph', icon: Network },
  { name: 'Vulnerabilities', href: '/vulnerabilities', icon: ShieldAlert },
  { name: 'Risk Analysis', href: '/risk', icon: Flame },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Settings & Audit', href: '/settings', icon: Settings },
];

export const Sidebar = ({ user, onOpenAuth }: { user: any; onOpenAuth: () => void }) => {
  const pathname = usePathname();

  const handleLogout = () => {
    api.removeToken();
    window.location.reload();
  };

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800 bg-slate-950/95 backdrop-blur-xl">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 shadow-lg shadow-cyan-500/20">
          <Network className="h-5 w-5 text-white" />
        </div>
        <div>
          <span className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
            Dependency<span className="text-cyan-400">X</span>
          </span>
          <span className="block text-[10px] font-medium tracking-wider text-slate-400 uppercase">
            Risk Map &bull; DP-900
          </span>
        </div>
      </div>

      {/* Cloud & Architecture Badge */}
      <div className="mx-4 mt-4 rounded-lg border border-cyan-900/40 bg-cyan-950/20 p-2.5">
        <div className="flex items-center gap-2 text-xs font-semibold text-cyan-300">
          <Cloud className="h-4 w-4 text-cyan-400" />
          <span>Azure Data Services</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400 leading-tight">
          Azure SQL 3NF Relational DB &bull; Blob Storage Manifests
        </p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <item.icon className={`h-4 w-4 transition-colors ${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* User / Authentication Status Footer */}
      <div className="border-t border-slate-800 p-4">
        {user ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 border border-slate-700 text-cyan-400">
                <UserIcon className="h-4 w-4" />
              </div>
              <div className="overflow-hidden">
                <p className="truncate text-xs font-semibold text-slate-200">{user.full_name || user.email}</p>
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                  <span className="text-[10px] text-slate-400 uppercase font-medium">{user.role}</span>
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-rose-400 transition"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-600/30 hover:bg-cyan-500 transition"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>Sign In / Demo Login</span>
          </button>
        )}
      </div>
    </aside>
  );
};
