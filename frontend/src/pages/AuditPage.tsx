import React from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { AuditLogTimeline } from '../components/AuditLogTimeline';
import { History, ShieldCheck, Download, RefreshCw } from 'lucide-react';
import { formatDateTime } from '../utils/formatters';

export const AuditPage: React.FC = () => {
  const { auditLogs, refresh } = useDashboardData();

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <History className="w-5 h-5 text-sky-400" />
            <span>OPERATIONAL AUDIT TRAIL</span>
          </h1>
          <p className="text-xs text-slate-400">
            Immutable chronological logging of dispatches, telemetry shifts, and coordinator interventions.
          </p>
        </div>
        <button
          onClick={refresh}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="rounded-xl bg-ops-card border border-ops-border overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-[11px] font-mono uppercase text-slate-400 border-b border-ops-border">
              <tr>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4">Result / Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-sky-400 font-medium whitespace-nowrap">
                      {formatDateTime(log.timestamp)}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-200">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xl">{log.description}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-950/60 text-amber-400 border-amber-500/30'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-500">
                    No audit records logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
