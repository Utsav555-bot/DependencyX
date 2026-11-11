'use client';

import React, { useState } from 'react';
import { X, ShieldCheck, Lock, Mail, User, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { api } from '../services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: any) => void;
}

export const AuthModal = ({ isOpen, onClose, onSuccess }: AuthModalProps) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'admin' | 'developer'>('developer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let data;
      if (isRegister) {
        data = await api.register({
          email,
          password,
          full_name: fullName,
          role,
          organization_name: 'Acme CyberSec'
        });
      } else {
        data = await api.login({ email, password });
      }
      onSuccess(data);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (demoRole: 'admin' | 'developer') => {
    setError(null);
    setLoading(true);
    const demoEmail = demoRole === 'admin' ? 'admin@dependencyx.io' : 'developer@dependencyx.io';
    try {
      const data = await api.login({ email: demoEmail, password: 'Password123!' });
      onSuccess(data);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-cyan-500/20 p-2 text-cyan-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                {isRegister ? 'Register Security Account' : 'Sign In to DependencyX'}
              </h3>
              <p className="text-xs text-slate-400">Software Dependency Risk Map</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Quick Demo Login Buttons */}
        <div className="mt-4 rounded-xl border border-cyan-900/40 bg-cyan-950/20 p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-300 mb-2">
            <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
            <span>Instant Evaluator Demo Access</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemoLogin('admin')}
              disabled={loading}
              className="rounded-lg border border-cyan-700/50 bg-cyan-900/40 px-2.5 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-800/50 transition disabled:opacity-50"
            >
              Sign In as Admin
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemoLogin('developer')}
              disabled={loading}
              className="rounded-lg border border-slate-700 bg-slate-800/60 px-2.5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
            >
              Sign In as Developer
            </button>
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Security Specialist"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">System Role</label>
              <select
                value={role}
                onChange={(e: any) => setRole(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
              >
                <option value="developer">Developer (Upload & View Scans)</option>
                <option value="admin">Security Admin (Full Org Management)</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-600/30 hover:bg-cyan-500 transition disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            <span>{isRegister ? 'Complete Registration' : 'Sign In'}</span>
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => { setIsRegister(!isRegister); setError(null); }}
            className="text-xs text-cyan-400 hover:underline"
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
};
