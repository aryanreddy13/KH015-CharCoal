import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { CommandLayout } from './layouts/CommandLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ZonesPage } from './pages/ZonesPage';
import { ResourcesPage } from './pages/ResourcesPage';
import { AllocationsPage } from './pages/AllocationsPage';
import { ReportsPage } from './pages/ReportsPage';
import { AlertsPage } from './pages/AlertsPage';
import { AuditPage } from './pages/AuditPage';
import { AgenciesPage } from './pages/AgenciesPage';
import { ReporterPage } from './pages/ReporterPage';
import { ProviderDashboardPage } from './pages/ProviderDashboardPage';

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Standalone Citizen / Field Mobile Reporter */}
      <Route path="/report" element={<ReporterPage />} />

      {/* Emergency Service Provider Operations Console */}
      <Route path="/provider" element={<ProviderDashboardPage />} />

      {/* Main Authority Command Center Layout */}
      <Route element={<CommandLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/zones" element={<ZonesPage />} />
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/allocations" element={<AllocationsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/agencies" element={<AgenciesPage />} />
      </Route>

      {/* Fallback routes */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
