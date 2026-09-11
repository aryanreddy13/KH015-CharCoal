import React from 'react';
import { AuditLog } from '../types';
import { History, ShieldCheck, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';
import { formatTimestamp } from '../utils/formatters';

interface AuditLogTimelineProps {
  logs: AuditLog[];
}

export const AuditLogTimeline: React.FC<AuditLogTimelineProps> = ({ logs }) => {
  const getEventBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SUCCESS':
        return {
          icon: ShieldCheck,
          color: 'text-emerald-400',
          bg: 'bg-emerald-950/40 border-emerald-500/30',
        };
      case 'WARNING':
        return {
          icon: AlertTriangle,
          color: 'text-amber-400',
          bg: 'bg-amber-950/40 border-amber-500/30',
        };
      case 'FAILURE':
        return {
          icon: XCircle,
          color: 'text-rose-400',
          bg: 'bg-rose-950/40 border-rose-500/30',
        };
      default:
        return {
          icon: History,
          color: 'text-sky-400',
          bg: 'bg-slate-900 border-slate-700',
        };
    }
  };

  return (
    <div className="rounded-xl bg-ops-card border border-ops-border p-4 space-y-3 shadow-md flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-ops-border pb-2.5">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-sky-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            System Operations Audit Trail
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400">Live Telemetry Feed</span>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[300px] pr-1">
        {logs.length > 0 ? (
          logs.map((log) => {
            const badge = getEventBadge(log.status);
            const Icon = badge.icon;
            return (
              <div
                key={log.id}
                className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 flex items-start space-x-3 text-xs"
              >
                {/* Timestamp */}
                <div className="font-mono text-[11px] font-bold text-sky-400 whitespace-nowrap pt-0.5">
                  {formatTimestamp(log.timestamp)}
                </div>

                <div className="flex-1 space-y-0.5">
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${badge.bg} ${badge.color}`}
                    >
                      {log.event_type}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                    {log.description}
                  </p>
                </div>

                <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${badge.color} mt-0.5`} />
              </div>
            );
          })
        ) : (
          <div className="p-4 rounded-lg bg-slate-900/40 text-center text-xs text-slate-500 italic">
            No audit events recorded yet.
          </div>
        )}
      </div>
    </div>
  );
};
