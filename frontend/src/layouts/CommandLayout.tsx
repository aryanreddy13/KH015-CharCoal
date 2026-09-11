import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { useDashboardData } from '../hooks/useDashboardData';

export const CommandLayout: React.FC = () => {
  const { isConnected, alerts, refresh } = useDashboardData();

  return (
    <div className="flex flex-col h-screen bg-ops-bg text-slate-100 overflow-hidden">
      {/* Top Operations Header */}
      <Navbar
        isConnected={isConnected}
        onRefresh={refresh}
        activeAlertCount={alerts.filter((a) => a.is_active).length}
      />

      {/* Body: Sidebar + Main Content View */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-5 bg-slate-950/40">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
