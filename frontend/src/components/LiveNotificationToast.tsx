import React, { useEffect } from 'react';
import { ShieldAlert, FileSpreadsheet, X, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface LiveNotificationToastProps {
  toast: {
    id: string;
    title: string;
    description: string;
    type: string;
    time: string;
  } | null;
  onClose: () => void;
}

export const LiveNotificationToast: React.FC<LiveNotificationToastProps> = ({ toast, onClose }) => {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, 8000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  const isSOS = toast.type === 'SOS';

  return (
    <div className="fixed top-20 right-6 z-50 max-w-sm w-full animate-in slide-in-from-top-4 duration-300">
      <div
        className={`p-4 rounded-xl border shadow-2xl backdrop-blur-md flex items-start gap-3 relative ${
          isSOS
            ? 'bg-rose-950/95 border-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.4)] text-white'
            : 'bg-sky-950/95 border-sky-500 shadow-[0_0_30px_rgba(56,189,248,0.3)] text-white'
        }`}
      >
        <div
          className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
            isSOS
              ? 'bg-rose-600 text-white animate-pulse'
              : 'bg-sky-600 text-white'
          }`}
        >
          {isSOS ? <ShieldAlert className="w-5 h-5" /> : <FileSpreadsheet className="w-5 h-5" />}
        </div>

        <div className="flex-1 min-w-0 pr-4">
          <div className="flex items-center justify-between gap-1 mb-1">
            <span
              className={`text-[10px] font-mono font-extrabold uppercase px-1.5 py-0.5 rounded ${
                isSOS
                  ? 'bg-rose-500/30 text-rose-200 border border-rose-400/40'
                  : 'bg-sky-500/30 text-sky-200 border border-sky-400/40'
              }`}
            >
              {isSOS ? 'LIVE SOS INTAKE' : 'NEW CITIZEN REPORT'}
            </span>
            <span className="text-[10px] font-mono text-slate-300">{toast.time}</span>
          </div>

          <h4 className="text-xs font-bold font-mono truncate text-white">{toast.title}</h4>
          <p className="text-[11px] text-slate-200 mt-0.5 line-clamp-2 leading-tight">
            {toast.description}
          </p>

          <div className="mt-2.5 flex items-center gap-2">
            <Link
              to="/reports"
              onClick={onClose}
              className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded transition flex items-center gap-1 ${
                isSOS
                  ? 'bg-rose-600 hover:bg-rose-500 text-white'
                  : 'bg-sky-600 hover:bg-sky-500 text-white'
              }`}
            >
              <span>Review in Intake Console</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-slate-400 hover:text-white transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
