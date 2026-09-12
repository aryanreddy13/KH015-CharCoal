import React from 'react';
import { Report } from '../types';
import { StatusBadge } from './StatusBadge';
import { ServicesNeededStack } from './ServicesNeededStack';
import { formatDateTime } from '../utils/formatters';
import {
  FileSpreadsheet,
  MapPin,
  Users,
  CheckCircle2,
  Send,
  Phone,
  ArrowRight,
  Radio,
  Image as ImageIcon,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface LiveCitizenReportsFeedProps {
  reports: Report[];
  onAcceptReport?: (reportId: string) => void;
  onDispatchReport?: (reportId: string) => void;
}

export const LiveCitizenReportsFeed: React.FC<LiveCitizenReportsFeedProps> = ({
  reports,
  onAcceptReport,
  onDispatchReport,
}) => {
  const pendingOrRecent = reports.slice(0, 6);

  return (
    <div className="rounded-xl bg-ops-card border border-ops-border overflow-hidden shadow-md flex flex-col h-full">
      {/* Feed Header */}
      <div className="p-3.5 border-b border-ops-border flex items-center justify-between bg-gradient-to-r from-ops-card via-slate-900 to-ops-card">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <FileSpreadsheet className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span>Live Citizen Field Intel & SOS Intake</span>
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            </h2>
            <p className="text-[10px] text-slate-400">
              Direct telemetry from mobile citizen app and field reporters
            </p>
          </div>
        </div>

        <Link
          to="/reports"
          className="text-[11px] font-mono font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1 bg-sky-950/40 border border-sky-500/30 px-2 py-1 rounded transition"
        >
          <span>View All ({reports.length})</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Reports List */}
      <div className="p-3 space-y-3 overflow-y-auto max-h-[500px] flex-1 divide-y divide-slate-800/60">
        {pendingOrRecent.length > 0 ? (
          pendingOrRecent.map((report) => {
            const isPending = report.status === 'PENDING REVIEW';
            return (
              <div
                key={report.id}
                className="pt-3 first:pt-0 flex flex-col gap-2.5 bg-slate-900/40 p-3 rounded-xl border border-slate-800/70 hover:border-slate-700 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] font-mono font-bold text-rose-400 bg-rose-950/70 border border-rose-500/30 px-2 py-0.5 rounded">
                      {report.disaster_type}
                    </span>
                    <StatusBadge status={report.status} />
                    {report.photo_url && (
                      <span className="text-[10px] font-mono text-sky-300 bg-sky-950/50 border border-sky-500/30 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <ImageIcon className="w-2.5 h-2.5 text-sky-400" />
                        <span>Photo Attached</span>
                      </span>
                    )}
                    <span className="text-[10px] font-mono text-slate-400">
                      {formatDateTime(report.created_at)}
                    </span>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-auto">
                    {isPending && onAcceptReport && (
                      <button
                        onClick={() => onAcceptReport(report.id)}
                        className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-mono font-bold flex items-center gap-1 shadow-sm transition"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Accept</span>
                      </button>
                    )}
                    {onDispatchReport && (
                      <button
                        onClick={() => onDispatchReport(report.id)}
                        className="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-[11px] font-mono font-bold flex items-center gap-1 shadow-sm transition"
                      >
                        <Send className="w-3 h-3" />
                        <span>Dispatch</span>
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-200 font-sans leading-relaxed">
                  "{report.description}"
                </p>

                {/* Services Needed Stack Component */}
                <ServicesNeededStack report={report} variant="compact" />

                {/* Metadata row */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="flex items-center gap-1 text-slate-300">
                      <Users className="w-3 h-3 text-sky-400" />
                      <span>~{report.people_affected || 1} affected</span>
                    </span>

                    {report.injured_people ? (
                      <span className="text-amber-400 font-bold">
                        {report.injured_people} injured
                      </span>
                    ) : null}

                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-rose-400" />
                      <span>
                        {report.latitude.toFixed(4)}°, {report.longitude.toFixed(4)}°
                      </span>
                    </span>

                    {report.reporter_phone && (
                      <span className="flex items-center gap-1 text-emerald-400">
                        <Phone className="w-2.5 h-2.5" />
                        <span>{report.reporter_phone}</span>
                      </span>
                    )}
                  </div>

                  <span className="text-slate-500 text-[10px]">
                    Reporter: {report.reporter_name || 'Citizen'}
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-8 text-center text-slate-500 font-mono text-xs">
            No citizen reports received yet. Submissions from phones will appear here automatically.
          </div>
        )}
      </div>
    </div>
  );
};
