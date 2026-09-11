import React from 'react';
import { Alert } from '../types';
import { AlertOctagon, AlertTriangle, Info, BellRing, Clock } from 'lucide-react';
import { formatTimestamp } from '../utils/formatters';

interface LiveAlertsFeedProps {
  alerts: Alert[];
}

export const LiveAlertsFeed: React.FC<LiveAlertsFeedProps> = ({ alerts }) => {
  const getAlertBadge = (level: string) => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return {
          icon: AlertOctagon,
          bg: 'bg-rose-950/70 border-rose-500/50 text-rose-300',
          indicator: 'bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]',
        };
      case 'WARNING':
        return {
          icon: AlertTriangle,
          bg: 'bg-amber-950/70 border-amber-500/50 text-amber-300',
          indicator: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]',
        };
      default:
        return {
          icon: Info,
          bg: 'bg-sky-950/70 border-sky-500/50 text-sky-300',
          indicator: 'bg-sky-500 shadow-[0_0_8px_rgba(56,189,248,0.8)]',
        };
    }
  };

  return (
    <div className="rounded-xl bg-ops-card border border-ops-border p-4 space-y-3 shadow-md flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-ops-border pb-2.5">
        <div className="flex items-center space-x-2">
          <BellRing className="w-4 h-4 text-rose-500 animate-bounce" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Live Priority Alerts
          </h2>
        </div>
        <span className="text-[11px] font-mono text-rose-400 font-bold">
          {alerts.filter((a) => a.is_active).length} Active
        </span>
      </div>

      <div className="space-y-2.5 overflow-y-auto max-h-[300px] pr-1">
        {alerts.length > 0 ? (
          alerts.map((alert) => {
            const badge = getAlertBadge(alert.alert_level);
            const Icon = badge.icon;
            return (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border ${badge.bg} transition-all duration-200 space-y-1.5`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${badge.indicator}`} />
                    <Icon className="w-3.5 h-3.5" />
                    <span className="font-bold text-xs tracking-tight">{alert.title}</span>
                  </div>
                  <div className="flex items-center space-x-1 text-[10px] font-mono opacity-75">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(alert.created_at)}</span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-200 leading-relaxed font-sans pl-4">
                  {alert.message}
                </p>
              </div>
            );
          })
        ) : (
          <div className="p-4 rounded-lg bg-slate-900/40 text-center text-xs text-slate-500 italic">
            No active threat alerts broadcasted.
          </div>
        )}
      </div>
    </div>
  );
};
