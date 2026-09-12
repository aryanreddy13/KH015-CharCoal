import React from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { KpiCards } from '../components/KpiCards';
import { DisasterMap } from '../components/DisasterMap';
import { ZoneDetailsDrawer } from '../components/ZoneDetailsDrawer';
import { CriticalNeedsList } from '../components/CriticalNeedsList';
import { ActiveAllocationsTable } from '../components/ActiveAllocationsTable';
import { LiveAlertsFeed } from '../components/LiveAlertsFeed';
import { AuditLogTimeline } from '../components/AuditLogTimeline';
import { SimulationControls } from '../components/SimulationControls';
import { ResourceAllocationOverview } from '../components/ResourceAllocationOverview';
import { LiveCitizenReportsFeed } from '../components/LiveCitizenReportsFeed';
import { Loader2, AlertCircle } from 'lucide-react';


export const DashboardPage: React.FC = () => {
  const {
    zones,
    resources,
    allocations,
    alerts,
    auditLogs,
    reports,
    kpi,
    selectedZone,
    selectedZoneId,
    setSelectedZoneId,
    loading,
    error,
    refresh,
    acceptReport,
    dispatchReport,
  } = useDashboardData();

  if (loading && zones.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-3 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-rose-500" />
        <p className="font-mono text-sm">Initializing Command Operations Telemetry...</p>
      </div>
    );
  }

  if (error && zones.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4 max-w-md mx-auto text-center">
        <div className="p-3 rounded-full bg-rose-950/80 border border-rose-500/50 text-rose-400">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h2 className="text-base font-bold text-white">Backend Connection Error</h2>
        <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
        <button
          onClick={refresh}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* KPI Stats Bar */}
      <KpiCards kpi={kpi} />

      {/* Simulation Controls Strip */}
      <SimulationControls onTriggerSuccess={refresh} />

      {/* Emergency Service Provider Pipeline Live Status Banner */}
      <div className="bg-ops-card border border-ops-border rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md bg-gradient-to-r from-sky-950/20 via-ops-card to-rose-950/20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <span className="font-black text-xs font-mono">ESP</span>
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase flex items-center gap-2">
              <span>Emergency Service Provider Mesh & Escalation Pipeline</span>
              <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] px-2 py-0.5 rounded-full">
                ● ACTIVE
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Auto-routing to Fire & Rescue, Medical, Police, and NGOs with Resend Email, PagerDuty, and Tactical Consoles.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="bg-slate-900 border border-slate-700/80 px-2.5 py-1 rounded text-slate-300 font-mono text-[11px]">
            📧 Resend: <strong className="text-emerald-400 font-bold">Enabled</strong>
          </span>
          <span className="bg-slate-900 border border-slate-700/80 px-2.5 py-1 rounded text-slate-300 font-mono text-[11px]">
            📞 PagerDuty: <strong className="text-emerald-400 font-bold">Connected</strong>
          </span>
          <span className="bg-slate-900 border border-slate-700/80 px-2.5 py-1 rounded text-slate-300 font-mono text-[11px]">
            📷 Evidence Storage: <strong className="text-sky-400 font-bold">Supabase</strong>
          </span>
          <a
            href="/provider"
            className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-3 py-1 rounded transition flex items-center gap-1 shadow-sm text-[11px]"
          >
            Launch Provider Console →
          </a>
        </div>
      </div>

      {/* Live Citizen & Mobile SOS Reports Stream */}
      <LiveCitizenReportsFeed
        reports={reports}
        onAcceptReport={acceptReport}
        onDispatchReport={dispatchReport}
      />

      {/* Real-time Multi-Agency Resource Allotment & Stock Monitor */}
      <ResourceAllocationOverview />

      {/* Main Operations Grid: Map & Live Zone Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        <div className="lg:col-span-7 xl:col-span-8 h-[460px]">
          <DisasterMap
            zones={zones}
            selectedZoneId={selectedZoneId}
            onSelectZone={setSelectedZoneId}
            resources={resources}
            allocations={allocations}
          />
        </div>

        <div className="lg:col-span-5 xl:col-span-4 h-[460px] overflow-y-auto">
          <ZoneDetailsDrawer
            zone={selectedZone}
            allocations={allocations}
          />
        </div>
      </div>

      {/* Critical Needs Manifest */}
      <CriticalNeedsList zones={zones} onSelectZone={setSelectedZoneId} />

      {/* Active Deployments Table */}
      <ActiveAllocationsTable
        allocations={allocations}
        zones={zones}
        onSelectZone={setSelectedZoneId}
      />

      {/* Real-time Feeds Row: Alerts & Activity Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch">
        <LiveAlertsFeed alerts={alerts} />
        <AuditLogTimeline logs={auditLogs} />
      </div>
    </div>
  );
};
