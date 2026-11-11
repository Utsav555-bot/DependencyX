'use client';

import React, { useState, useEffect } from 'react';
import './globals.css';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { ProjectUploadModal } from '../components/ProjectUploadModal';
import { AuthModal } from '../components/AuthModal';
import { api } from '../services/api';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const refreshUser = () => {
    const stored = api.getStoredUser();
    if (stored) {
      setUser(stored);
    } else {
      // Default to demo admin on fresh session for convenience
      api.login({ email: 'admin@dependencyx.io', password: 'Password123!' })
        .then((data) => setUser(data))
        .catch(() => {});
    }
  };

  const loadProjects = () => {
    api.getProjects()
      .then((data) => setProjects(data))
      .catch(() => {});
  };

  useEffect(() => {
    refreshUser();
    loadProjects();
  }, []);

  const handleSwitchRole = async (role: 'admin' | 'developer') => {
    const targetEmail = role === 'admin' ? 'admin@dependencyx.io' : 'developer@dependencyx.io';
    try {
      const data = await api.login({ email: targetEmail, password: 'Password123!' });
      setUser(data);
      loadProjects();
    } catch (err) {
      console.error('Role switch error', err);
    }
  };

  return (
    <html lang="en" className="dark">
      <body className="bg-cyber-bg text-slate-100 antialiased">
        <div className="flex min-h-screen">
          {/* Left Sidebar */}
          <Sidebar user={user} onOpenAuth={() => setIsAuthOpen(true)} />

          {/* Main Area */}
          <div className="flex flex-1 flex-col pl-64">
            <Navbar
              onOpenCreateProject={() => setIsUploadOpen(true)}
              onRefresh={() => {
                refreshUser();
                loadProjects();
              }}
              user={user}
              onSwitchRole={handleSwitchRole}
            />

            <main className="flex-1 p-8">{children}</main>
          </div>
        </div>

        {/* Global Modals */}
        <ProjectUploadModal
          isOpen={isUploadOpen}
          onClose={() => setIsUploadOpen(false)}
          onSuccess={() => {
            loadProjects();
          }}
          projects={projects}
        />

        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onSuccess={(u) => {
            setUser(u);
            loadProjects();
          }}
        />
      </body>
    </html>
  );
}
