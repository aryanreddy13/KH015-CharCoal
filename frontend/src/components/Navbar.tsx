import React, { useState, useEffect } from 'react';
import { Radio, ShieldAlert, Bell, Clock, RefreshCw, Shield, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface NavbarProps {
  isConnected: boolean;
  onRefresh?: () => void;
  activeAlertCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ isConnected, onRefresh, activeAlertCount = 0 }) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }) + ' UTC'
      );
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 bg-ops-surface border-b border-ops-border flex items-center justify-between px-6 z-30 select-none">
      {/* Brand & System Title */}
      <div className="flex items-center space-x-4">
        <Link to="/dashboard" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-lg bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400 group-hover:scale-105 transition-transform shadow-[0_0_15px_rgba(244,63,94,0.3)]">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold tracking-wider text-rose-500 font-mono text-lg">PS20</span>
              <span className="text-xs bg-slate-800 text-slate-300 font-mono px-1.5 py-0.5 rounded border border-slate-700">
                v1.0-P1
              </span>
            </div>
            <h1 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Disaster Response Command Center
            </h1>
          </div>
        </Link>
      </div>

      {/* Center Operational Status */}
      <div className="hidden md:flex items-center space-x-6">
        <div className="flex items-center space-x-2 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-800 text-xs font-mono">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span className="text-slate-200 font-semibold">{timeStr}</span>
        </div>

        {/* Live WebSocket Indicator */}
        <div
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-medium ${
            isConnected
              ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-400'
              : 'bg-rose-950/50 border-rose-500/40 text-rose-400'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {isConnected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isConnected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            ></span>
          </span>
          <span>{isConnected ? 'TELEMETRY LIVE' : 'RECONNECTING'}</span>
        </div>
      </div>

      {/* Right User & Quick Actions */}
      <div className="flex items-center space-x-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Sync live telemetry"
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        <Link
          to="/provider"
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/40 font-bold text-xs transition-all"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-sky-400" />
          <span>Provider Console</span>
        </Link>

        <Link
          to="/report"
          className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-[0_0_10px_rgba(225,29,72,0.4)] transition-all"
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Citizen View</span>
        </Link>

        {/* Alerts Bell */}
        <Link
          to="/alerts"
          className="relative p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {activeAlertCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-[10px] font-bold text-white flex items-center justify-center">
              {activeAlertCount}
            </span>
          )}
        </Link>

        {/* Agency Operator Indicator */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-sky-950 border border-sky-500/40 flex items-center justify-center text-sky-400">
            <Shield className="w-4 h-4" />
          </div>
          <div className="hidden lg:block text-left text-xs">
            <div className="font-semibold text-slate-200">Cmdr. Vance</div>
            <div className="text-[10px] text-slate-400">Govt Emergency Services</div>
          </div>
        </div>
      </div>
    </header>
  );
};
