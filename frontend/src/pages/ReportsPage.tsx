import React, { useState, useEffect } from 'react';
import { Report } from '../types';
import { apiService } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { formatDateTime } from '../utils/formatters';
import { FileSpreadsheet, MapPin, Users, AlertCircle, RefreshCw } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await apiService.getReports();
      setReports(data);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div className="space-y-4 max-w-[1700px] mx-auto pb-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ops-border pb-3">
        <div>
          <h1 className="text-lg font-bold text-white font-mono flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-sky-400" />
            <span>CITIZEN & FIELD INCIDENT REPORTS</span>
          </h1>
          <p className="text-xs text-slate-400">
            Emergency submissions from mobile portal and on-ground spotters.
          </p>
        </div>
        <button
          onClick={fetchReports}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.length > 0 ? (
          reports.map((report) => (
            <div
              key={report.id}
              className="p-4 rounded-xl bg-ops-card border border-ops-border space-y-3 shadow-md"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-rose-400 px-2 py-0.5 rounded bg-rose-950/60 border border-rose-500/30">
                    {report.disaster_type}
                  </span>
                </div>
                <StatusBadge status={report.status} />
              </div>

              <p className="text-xs text-slate-200 leading-relaxed font-sans">{report.description}</p>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
                <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                  <div className="text-slate-400">Affected</div>
                  <div className="font-bold text-white text-sm">{report.people_affected}</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                  <div className="text-slate-400">Injured</div>
                  <div className="font-bold text-amber-400 text-sm">{report.injured_people}</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                  <div className="text-slate-400">Missing</div>
                  <div className="font-bold text-rose-400 text-sm">{report.missing_people}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
                <span className="flex items-center space-x-1">
                  <MapPin className="w-3 h-3 text-sky-400" />
                  <span>
                    {report.latitude.toFixed(3)}°, {report.longitude.toFixed(3)}°
                  </span>
                </span>
                <span>{formatDateTime(report.created_at)}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-3 py-12 text-center text-slate-500">
            No citizen reports received yet.
          </div>
        )}
      </div>
    </div>
  );
};
