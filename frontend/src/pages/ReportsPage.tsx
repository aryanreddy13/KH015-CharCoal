import React, { useState, useMemo } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { StatusBadge } from '../components/StatusBadge';
import { formatDateTime } from '../utils/formatters';
import {
  FileSpreadsheet,
  MapPin,
  Users,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Send,
  Check,
  XCircle,
  Phone,
  User,
  Image as ImageIcon,
  MessageSquare,
  Search,
  SlidersHorizontal,
  Radio,
  ExternalLink,
  Trash2,
  Clock,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';
import { Report } from '../types';

export const ReportsPage: React.FC = () => {
  const {
    reports,
    loading,
    isConnected,
    refresh,
    acceptReport,
    dispatchReport,
    resolveReport,
    dismissReport,
    deleteReport,
  } = useDashboardData();

  const [selectedStatusTab, setSelectedStatusTab] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDisasterType, setSelectedDisasterType] = useState('ALL');
  const [previewPhotoUrl, setPreviewPhotoUrl] = useState<string | null>(null);
  const [actioningId, setActioningId] = useState<string | null>(null);
  const [noteModalReport, setNoteModalReport] = useState<Report | null>(null);
  const [adminNoteText, setAdminNoteText] = useState('');

  // Status counts
  const counts = useMemo(() => {
    return {
      all: reports.length,
      pending: reports.filter((r) => r.status === 'PENDING REVIEW').length,
      verified: reports.filter((r) => r.status === 'VERIFIED' || r.status === 'ACCEPTED').length,
      actioned: reports.filter((r) => r.status === 'ACTIONED' || r.status === 'IN_PROGRESS').length,
      resolved: reports.filter((r) => r.status === 'RESOLVED').length,
      dismissed: reports.filter((r) => r.status === 'DISMISSED' || r.status === 'REJECTED').length,
    };
  }, [reports]);

  // Unique disaster types for filter
  const disasterTypes = useMemo(() => {
    const set = new Set<string>();
    reports.forEach((r) => {
      if (r.disaster_type) set.add(r.disaster_type);
    });
    return Array.from(set);
  }, [reports]);

  // Filtered reports list
  const filteredReports = useMemo(() => {
    return reports.filter((r) => {
      // Status filter
      if (selectedStatusTab === 'PENDING' && r.status !== 'PENDING REVIEW') return false;
      if (selectedStatusTab === 'VERIFIED' && r.status !== 'VERIFIED' && r.status !== 'ACCEPTED') return false;
      if (selectedStatusTab === 'ACTIONED' && r.status !== 'ACTIONED' && r.status !== 'IN_PROGRESS') return false;
      if (selectedStatusTab === 'RESOLVED' && r.status !== 'RESOLVED') return false;
      if (selectedStatusTab === 'DISMISSED' && r.status !== 'DISMISSED' && r.status !== 'REJECTED') return false;

      // Disaster type filter
      if (selectedDisasterType !== 'ALL' && r.disaster_type !== selectedDisasterType) return false;

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchType = r.disaster_type?.toLowerCase().includes(q);
        const matchDesc = r.description?.toLowerCase().includes(q);
        const matchName = r.reporter_name?.toLowerCase().includes(q);
        const matchPhone = r.reporter_phone?.toLowerCase().includes(q);
        const matchLoc = r.location_text?.toLowerCase().includes(q);
        if (!matchType && !matchDesc && !matchName && !matchPhone && !matchLoc) return false;
      }

      return true;
    });
  }, [reports, selectedStatusTab, selectedDisasterType, searchQuery]);

  const handleAccept = async (reportId: string) => {
    try {
      setActioningId(reportId);
      await acceptReport(reportId, 'Report verified and accepted for emergency action.');
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  const handleDispatch = async (reportId: string) => {
    try {
      setActioningId(reportId);
      await dispatchReport(reportId, { notes: 'Response convoy mobilized.' });
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  const handleResolve = async (reportId: string) => {
    try {
      setActioningId(reportId);
      await resolveReport(reportId, 'Incident verified as resolved.');
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  const handleDismiss = async (reportId: string) => {
    try {
      setActioningId(reportId);
      await dismissReport(reportId, 'Report dismissed by administrator.');
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (window.confirm('Are you sure you want to permanently delete this citizen report?')) {
      try {
        setActioningId(reportId);
        await deleteReport(reportId);
      } catch (e) {
        console.error(e);
      } finally {
        setActioningId(null);
      }
    }
  };

  const handleSaveNote = async () => {
    if (!noteModalReport || !adminNoteText.trim()) return;
    try {
      setActioningId(noteModalReport.id);
      await acceptReport(noteModalReport.id, adminNoteText);
      setNoteModalReport(null);
      setAdminNoteText('');
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  return (
    <div className="space-y-5 max-w-[1700px] mx-auto pb-12">
      {/* Top Header & Live Telemetry Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-ops-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-extrabold tracking-wider text-sky-400 bg-sky-950/60 border border-sky-500/30 px-2 py-0.5 rounded">
              CITIZEN & FIELD INTELLIGENCE
            </span>
            <span
              className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center gap-1.5 border ${
                isConnected
                  ? 'bg-emerald-950/70 text-emerald-400 border-emerald-500/40'
                  : 'bg-amber-950/70 text-amber-400 border-amber-500/40'
              }`}
            >
              <Radio className="w-3 h-3 animate-pulse" />
              <span>{isConnected ? 'LIVE WEBSOCKET STREAMING' : 'CONNECTING...'}</span>
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-black text-white font-mono flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6 text-rose-500" />
            <span>INCIDENT REPORTS & CITIZEN INTAKE CONSOLE</span>
          </h1>
          <p className="text-xs text-slate-400">
            Real-time feed of disaster submissions from mobile citizen app and field spotters with instant verification & dispatch.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={refresh}
            disabled={loading}
            className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-200 text-xs font-mono flex items-center gap-2 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-rose-400' : 'text-slate-400'}`} />
            <span>SYNC NOW</span>
          </button>
        </div>
      </div>

      {/* Metric Counters Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
        <button
          onClick={() => setSelectedStatusTab('ALL')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'ALL'
              ? 'bg-slate-800/90 border-slate-500 shadow-md ring-1 ring-slate-400/40'
              : 'bg-ops-card border-ops-border hover:border-slate-700'
          }`}
        >
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Total Intake</div>
          <div className="text-xl font-black text-white mt-0.5">{counts.all}</div>
        </button>

        <button
          onClick={() => setSelectedStatusTab('PENDING')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'PENDING'
              ? 'bg-amber-950/70 border-amber-500 shadow-md ring-1 ring-amber-500/40'
              : 'bg-ops-card border-ops-border hover:border-amber-500/40'
          }`}
        >
          <div className="text-[11px] text-amber-400 uppercase font-semibold flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            <span>Pending Review</span>
          </div>
          <div className="text-xl font-black text-amber-400 mt-0.5">{counts.pending}</div>
        </button>

        <button
          onClick={() => setSelectedStatusTab('VERIFIED')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'VERIFIED'
              ? 'bg-emerald-950/70 border-emerald-500 shadow-md ring-1 ring-emerald-500/40'
              : 'bg-ops-card border-ops-border hover:border-emerald-500/40'
          }`}
        >
          <div className="text-[11px] text-emerald-400 uppercase font-semibold">Accepted / Verified</div>
          <div className="text-xl font-black text-emerald-400 mt-0.5">{counts.verified}</div>
        </button>

        <button
          onClick={() => setSelectedStatusTab('ACTIONED')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'ACTIONED'
              ? 'bg-sky-950/70 border-sky-500 shadow-md ring-1 ring-sky-500/40'
              : 'bg-ops-card border-ops-border hover:border-sky-500/40'
          }`}
        >
          <div className="text-[11px] text-sky-400 uppercase font-semibold">Dispatched / En Route</div>
          <div className="text-xl font-black text-sky-400 mt-0.5">{counts.actioned}</div>
        </button>

        <button
          onClick={() => setSelectedStatusTab('RESOLVED')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'RESOLVED'
              ? 'bg-teal-950/70 border-teal-500 shadow-md ring-1 ring-teal-500/40'
              : 'bg-ops-card border-ops-border hover:border-teal-500/40'
          }`}
        >
          <div className="text-[11px] text-teal-400 uppercase font-semibold">Resolved on Ground</div>
          <div className="text-xl font-black text-teal-400 mt-0.5">{counts.resolved}</div>
        </button>

        <button
          onClick={() => setSelectedStatusTab('DISMISSED')}
          className={`p-3 rounded-xl border text-left transition ${
            selectedStatusTab === 'DISMISSED'
              ? 'bg-slate-900 border-slate-600 shadow-md ring-1 ring-slate-500/40'
              : 'bg-ops-card border-ops-border hover:border-slate-700'
          }`}
        >
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Dismissed / Spam</div>
          <div className="text-xl font-black text-slate-400 mt-0.5">{counts.dismissed}</div>
        </button>
      </div>

      {/* Filters and Search Bar */}
      <div className="bg-ops-card border border-ops-border rounded-xl p-3 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-md">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by disaster type, citizen name, phone, description, or coords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900/90 border border-slate-700/80 text-white text-xs focus:outline-none focus:border-rose-500 font-sans"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400">Type:</span>
          <select
            value={selectedDisasterType}
            onChange={(e) => setSelectedDisasterType(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 text-xs focus:outline-none focus:border-rose-500"
          >
            <option value="ALL">All Disaster Types</option>
            {disasterTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredReports.length > 0 ? (
          filteredReports.map((report) => {
            const isPending = report.status === 'PENDING REVIEW';
            const isVerified = report.status === 'VERIFIED' || report.status === 'ACCEPTED';
            const isActioned = report.status === 'ACTIONED' || report.status === 'IN_PROGRESS';
            const isResolved = report.status === 'RESOLVED';
            const isDismissed = report.status === 'DISMISSED' || report.status === 'REJECTED';
            const isBusy = actioningId === report.id;

            return (
              <div
                key={report.id}
                className={`p-4 rounded-xl bg-ops-card border transition-all duration-200 flex flex-col justify-between shadow-md relative ${
                  isPending
                    ? 'border-amber-500/40 hover:border-amber-500/70 bg-gradient-to-b from-amber-950/10 to-ops-card'
                    : isVerified
                    ? 'border-emerald-500/30 hover:border-emerald-500/60'
                    : isActioned
                    ? 'border-sky-500/30 hover:border-sky-500/60'
                    : 'border-ops-border hover:border-slate-700'
                }`}
              >
                <div>
                  {/* Card Header: Type, Priority Score, Status */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs font-mono font-bold text-rose-400 px-2 py-0.5 rounded bg-rose-950/70 border border-rose-500/30 uppercase">
                        {report.disaster_type || 'Emergency'}
                      </span>
                      {report.priority_score && (
                        <span className="text-[10px] font-mono font-extrabold text-amber-300 bg-amber-950/60 border border-amber-500/30 px-1.5 py-0.5 rounded">
                          PRIO {report.priority_score.toFixed(1)}/10
                        </span>
                      )}
                    </div>
                    <StatusBadge status={report.status} />
                  </div>

                  {/* Citizen Description */}
                  <p className="text-xs text-slate-100 leading-relaxed font-sans bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80 mb-3">
                    "{report.description || 'No description provided.'}"
                  </p>

                  {/* Evidence Photo Preview if present */}
                  {report.photo_url && (
                    <div className="mb-3">
                      <div
                        onClick={() => setPreviewPhotoUrl(report.photo_url || null)}
                        className="group relative cursor-pointer overflow-hidden rounded-lg border border-slate-700/80 bg-slate-900 h-36 flex items-center justify-center"
                      >
                        <img
                          src={report.photo_url}
                          alt="Incident Evidence"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent flex items-end p-2 opacity-90 group-hover:opacity-100">
                          <span className="text-[10px] font-mono text-sky-300 flex items-center gap-1 bg-slate-900/80 px-2 py-0.5 rounded">
                            <ImageIcon className="w-3 h-3 text-sky-400" />
                            <span>Click to Zoom Photo Evidence</span>
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Impact Stats Grid */}
                  <div className="grid grid-cols-3 gap-2 mb-3 text-[11px] font-mono">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                      <div className="text-slate-400 text-[10px]">Affected</div>
                      <div className="font-bold text-white text-sm">{report.people_affected ?? 1}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                      <div className="text-slate-400 text-[10px]">Injured</div>
                      <div className="font-bold text-amber-400 text-sm">{report.injured_people ?? 0}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                      <div className="text-slate-400 text-[10px]">Missing</div>
                      <div className="font-bold text-rose-400 text-sm">{report.missing_people ?? 0}</div>
                    </div>
                  </div>

                  {/* Reporter & Location Metadata */}
                  <div className="space-y-1.5 text-[11px] font-mono text-slate-300 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/60 mb-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 flex items-center gap-1.5">
                        <User className="w-3 h-3 text-sky-400" />
                        <span>Reporter:</span>
                      </span>
                      <span className="font-bold text-slate-200">{report.reporter_name || 'Citizen'}</span>
                    </div>

                    {report.reporter_phone && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 flex items-center gap-1.5">
                          <Phone className="w-3 h-3 text-emerald-400" />
                          <span>Contact:</span>
                        </span>
                        <a
                          href={`tel:${report.reporter_phone}`}
                          className="text-emerald-400 hover:underline font-bold flex items-center gap-1"
                        >
                          <span>{report.reporter_phone}</span>
                        </a>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 flex items-center gap-1.5">
                        <MapPin className="w-3 h-3 text-rose-400" />
                        <span>GPS Coordinates:</span>
                      </span>
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${report.latitude},${report.longitude}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-400 hover:underline flex items-center gap-1"
                      >
                        <span>
                          {report.latitude.toFixed(4)}°, {report.longitude.toFixed(4)}°
                        </span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        <span>Received:</span>
                      </span>
                      <span>{formatDateTime(report.created_at)}</span>
                    </div>
                  </div>

                  {/* Admin notes if present */}
                  {report.admin_notes && (
                    <div className="text-[11px] font-mono text-slate-300 bg-sky-950/20 border border-sky-500/20 rounded-lg p-2 mb-3">
                      <div className="text-sky-400 font-bold text-[10px] uppercase flex items-center gap-1 mb-0.5">
                        <MessageSquare className="w-2.5 h-2.5" />
                        <span>Admin Action Log</span>
                      </div>
                      <div className="text-slate-300 whitespace-pre-line text-[10px]">{report.admin_notes}</div>
                    </div>
                  )}
                </div>

                {/* Dynamic Administrator Action Buttons */}
                <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-1.5 flex-1">
                    {/* Accept / Verify button */}
                    {isPending && (
                      <button
                        onClick={() => handleAccept(report.id)}
                        disabled={isBusy}
                        className="flex-1 min-w-[110px] py-1.5 px-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-[11px] font-bold flex items-center justify-center gap-1.5 transition shadow-sm"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Accept & Verify</span>
                      </button>
                    )}

                    {/* Dispatch Emergency Response */}
                    {(isPending || isVerified) && (
                      <button
                        onClick={() => handleDispatch(report.id)}
                        disabled={isBusy}
                        className="flex-1 min-w-[110px] py-1.5 px-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-mono text-[11px] font-bold flex items-center justify-center gap-1.5 transition shadow-sm"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Dispatch Units</span>
                      </button>
                    )}

                    {/* Mark Resolved */}
                    {(isVerified || isActioned) && !isResolved && (
                      <button
                        onClick={() => handleResolve(report.id)}
                        disabled={isBusy}
                        className="flex-1 min-w-[110px] py-1.5 px-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-mono text-[11px] font-bold flex items-center justify-center gap-1.5 transition shadow-sm"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Mark Resolved</span>
                      </button>
                    )}

                    {/* Dismiss / Reject */}
                    {!isDismissed && !isResolved && (
                      <button
                        onClick={() => handleDismiss(report.id)}
                        disabled={isBusy}
                        className="py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 border border-slate-700 hover:border-rose-500/40 text-slate-300 hover:text-rose-400 font-mono text-[11px] flex items-center gap-1 transition"
                      >
                        <XCircle className="w-3 h-3" />
                        <span>Dismiss</span>
                      </button>
                    )}
                  </div>

                  {/* Context Note & Delete */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setNoteModalReport(report);
                        setAdminNoteText('');
                      }}
                      title="Add Admin Response Note"
                      className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-600 text-slate-400 hover:text-white"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(report.id)}
                      title="Delete Report"
                      className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-rose-500/50 text-slate-400 hover:text-rose-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-full py-16 text-center text-slate-500 font-mono bg-ops-card border border-ops-border rounded-xl">
            <FileSpreadsheet className="w-10 h-10 mx-auto mb-2 text-slate-600" />
            <div className="text-sm text-slate-400 font-bold">No matching citizen reports found</div>
            <div className="text-xs text-slate-500 mt-1">
              Submissions from the citizen mobile application or field web portal will dynamically appear here in real-time.
            </div>
          </div>
        )}
      </div>

      {/* Photo Lightbox Modal */}
      {previewPhotoUrl && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4"
          onClick={() => setPreviewPhotoUrl(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden p-2 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setPreviewPhotoUrl(null)}
              className="absolute top-4 right-4 z-10 w-9 h-9 rounded-full bg-slate-950/80 border border-slate-700 text-white flex items-center justify-center hover:bg-rose-600 transition"
            >
              <XCircle className="w-5 h-5" />
            </button>
            <img
              src={previewPhotoUrl}
              alt="Disaster Evidence High Resolution"
              className="w-full max-h-[82vh] object-contain rounded-xl"
            />
            <div className="text-center py-2 text-xs font-mono text-slate-400">
              📷 Citizen On-Scene Photographic Evidence
            </div>
          </div>
        </div>
      )}

      {/* Add Admin Note Modal */}
      {noteModalReport && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setNoteModalReport(null)}
        >
          <div
            className="w-full max-w-md bg-ops-card border border-slate-700 rounded-2xl p-5 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-mono font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-sky-400" />
                <span>Add Admin Response Note</span>
              </h3>
              <button
                onClick={() => setNoteModalReport(null)}
                className="text-slate-400 hover:text-white"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs text-slate-300">
              Attach verification instructions, resource assignments, or tactical briefing notes to report{' '}
              <strong className="text-white font-mono">{noteModalReport.id.slice(0, 8)}</strong> (
              {noteModalReport.disaster_type}).
            </div>

            <textarea
              rows={4}
              placeholder="e.g. Field spotters confirmed water level rising by 1.2m. Dispatched 2 inflatable rescue boats from Station 4."
              value={adminNoteText}
              onChange={(e) => setAdminNoteText(e.target.value)}
              className="w-full p-3 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-sky-500 font-sans leading-relaxed"
            />

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setNoteModalReport(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-mono font-bold flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Save Note</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
